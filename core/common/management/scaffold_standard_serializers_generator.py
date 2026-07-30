from pathlib import Path

from django.db import models

from core.common.management import scaffold_standard_api_generator as gen


def _serializer_import_path_for(target_model: type[models.Model], *, ctx: gen.ScaffoldContext) -> str | None:
    """Return the python import path to use for ``{Model}CompactSerializer`` of ``target_model``.

    Self-references (``target_model is ctx.model``) return ``None`` — the resource module
    imports its compact from ``from .compacts import <Model>CompactSerializer``.

    Same-app targets use **``core.<app>.serializers.compacts``** (leaf module; no sibling
    resource serializer imports) to avoid circular imports.

    Cross-app targets use the **app serializer barrel** (``core.<otherapp>.serializers``).
    """
    if target_model is ctx.model:
        return None
    module = target_model.__module__
    if ".models" not in module:
        return None
    target_app_path = module.split(".models", 1)[0]
    if target_app_path == ctx.app_python_path:
        return f"{target_app_path}.serializers.compacts"
    return f"{target_app_path}.serializers"


def _iter_resource_fks(ctx: gen.ScaffoldContext):
    yield from ctx.foreign_keys
    yield from ctx.m2m_fields

    def walk(dependents: list[gen.DependentSpec]):
        for dep in dependents:
            if dep.is_reference_domain_resource:
                # The reference resource ships its own compact serializer; we don't render
                # its FKs / M2Ms or its sub-children on the parent.
                continue
            yield from dep.child_fks
            yield from dep.child_m2m
            yield from walk(dep.children)

    yield from walk(ctx.dependents)


def _reference_domain_resource_compact_imports(ctx: gen.ScaffoldContext) -> list[str]:
    """Imports for ``{Model}CompactSerializer`` of cascade children that are independent REST resources.

    Same-app references resolve to ``core.<app>.serializers.<snake>``; cross-app references
    resolve to ``core.<otherapp>.serializers`` (the barrel). See ``_serializer_import_path_for``.
    """
    grouped: dict[str, set[str]] = {}

    def walk(deps: list[gen.DependentSpec]) -> None:
        for dep in deps:
            if dep.is_reference_domain_resource:
                path = _serializer_import_path_for(dep.child_model, ctx=ctx)
                if path is None:
                    continue
                ser_name = f"{dep.child_model.__name__}CompactSerializer"
                grouped.setdefault(path, set()).add(ser_name)
                continue
            walk(dep.children)

    walk(ctx.dependents)
    return _format_grouped_imports(grouped)


def _resource_compact_imports(ctx: gen.ScaffoldContext) -> list[str]:
    """``{Model}CompactSerializer`` imports for every non-special FK / M2M referenced.

    Same-app vs. cross-app resolution mirrors ``_reference_domain_resource_compact_imports``
    so the file never imports a same-app sibling through the barrel.
    """
    grouped: dict[str, set[str]] = {}
    for fk in _iter_resource_fks(ctx):
        if (
            gen._fk_related_is_terminology_concept(fk)
            or gen._fk_related_is_content_type(fk)
            or gen._fk_related_is_user(fk)
        ):
            continue
        path = _serializer_import_path_for(fk.related_model, ctx=ctx)
        if path is None:
            continue
        ser_name = f"{fk.related_model.__name__}CompactSerializer"
        grouped.setdefault(path, set()).add(ser_name)
    return _format_grouped_imports(grouped)


def _format_grouped_imports(grouped: dict[str, set[str]]) -> list[str]:
    """Stable, readable ``from <path> import …`` rendering for grouped serializer names."""
    imports: list[str] = []
    for path in sorted(grouped):
        names = sorted(grouped[path])
        if len(names) == 1:
            imports.append(f"from {path} import {names[0]}")
        else:
            imports.append(f"from {path} import (")
            imports.extend(f"    {name}," for name in names)
            imports.append(")")
    return imports


def _resource_datatype_imports(ctx: gen.ScaffoldContext) -> list[str]:
    """Emit a single ``from core.common.data_types.serializers import (...)`` block.

    The bundled barrel re-exports every datatype trio, so generated files import every
    used datatype serializer through one import statement. Bases are discovered from
    the cascade tree (skipping reference domain resources) and resolved against the
    shared ``DATATYPE_ABSTRACT_TO_SERIALIZERS`` map so the import set always tracks
    actual usage and picks up new datatypes automatically as they're added.
    """
    needed: set[str] = set()

    def collect_datatype_bases(deps: list[gen.DependentSpec]) -> None:
        for dep in deps:
            if dep.datatype_base:
                needed.add(dep.datatype_base)
            if dep.is_reference_domain_resource:
                continue
            collect_datatype_bases(dep.children)

    collect_datatype_bases(ctx.dependents)

    names: set[str] = set()
    for base in needed:
        trio = gen.DATATYPE_ABSTRACT_TO_SERIALIZERS.get(base)
        if trio is None:
            continue
        output_name, create_name, update_name = trio
        names.update((create_name, output_name, update_name))
    if not names:
        return []

    imports = ["from core.common.data_types.serializers import ("]
    imports.extend(f"    {name}," for name in sorted(names))
    imports.append(")")
    return imports


def _content_type_helper_imports(ctx: gen.ScaffoldContext) -> list[str]:
    """``ContentTypeCompactSerializer`` / ``ContentTypeNaturalKeyField`` imports when used.

    Generic-FK fields render as ``ContentTypeNaturalKeyField`` on create/update inputs
    (natural-key string ``"<app_label>.<model>"``) and as ``ContentTypeCompactSerializer``
    on list/detail outputs. Both live in ``core.api.serializers`` and must be imported
    explicitly — they are not part of the resource's own serializer file.

    Detection covers top-level FKs as well as FKs on cascade-owned dependents (e.g.
    ``deleted_by``-style audit FKs on a child row).
    """
    if not (gen._context_has_content_type_fk(ctx) or gen._any_dep_has_content_type_fk(ctx.dependents)):
        return []
    return ["from core.api.serializers import ContentTypeCompactSerializer, ContentTypeNaturalKeyField"]


def _choices_owner_model_imports(ctx: gen.ScaffoldContext) -> list[str]:
    """Imports for model classes that own ``models.Choices`` enums referenced as ``Parent.Enum.choices``.

    The scaffold emits ``serializers.ChoiceField(choices=<Parent>.<Enum>.choices)`` for
    fields whose ``.choices`` matches a nested ``models.Choices`` subclass. ``<Parent>``
    must be importable in the generated serializer file — usually the resource model
    itself, but any concrete model in the MRO is supported.
    """
    parents = gen._collect_unique_choices_parent_classes(ctx)
    if not parents:
        return []
    grouped: dict[str, set[str]] = {}
    for cls in parents:
        module = gen._top_pkg(cls.__module__)
        grouped.setdefault(module, set()).add(cls.__name__)
    return _format_grouped_imports(grouped)


def _serializer_imports(ctx: gen.ScaffoldContext) -> str:
    parts: list[str] = [
        "from rest_framework import serializers",
        "",
        "from core.api.mixins import ListOrderingMixin",
    ]
    utils_imports = ["inline_serializer"]
    if gen._has_optional_query_boolean_filter(ctx):
        utils_imports.insert(0, "OptionalQueryBooleanField")
    parts.append(f"from core.api.utils import {', '.join(utils_imports)}")
    parts.extend([
        "from core.users.serializers import UserCompactSerializer",
        "",
    ])

    content_type_imports = _content_type_helper_imports(ctx)
    parts.extend(content_type_imports)
    if content_type_imports:
        parts.append("")

    datatype_imports = _resource_datatype_imports(ctx)
    parts.extend(datatype_imports)
    if datatype_imports:
        parts.append("")

    resource_imports = _resource_compact_imports(ctx)
    parts.extend(resource_imports)
    if resource_imports:
        parts.append("")

    reference_compact_imports = _reference_domain_resource_compact_imports(ctx)
    parts.extend(reference_compact_imports)
    if reference_compact_imports:
        parts.append("")

    choices_owner_imports = _choices_owner_model_imports(ctx)
    parts.extend(choices_owner_imports)
    if choices_owner_imports:
        parts.append("")

    if ctx.has_history:
        parts.append("from core.api.serializers import RevisionSerializer")
        parts.append("from drf_spectacular.utils import extend_schema_serializer")
        parts.append("")

    return "\n".join(parts)


def _compact_output_lines(ctx: gen.ScaffoldContext) -> list[str]:
    lines = ["        id = serializers.UUIDField()"]
    if ctx.reference_id_field is not None:
        lines.append("        reference_id = serializers.CharField(required=False, allow_blank=True)")
    for item in ctx.scalar_fields:
        if item.name in {"name", "title", "code", "display"}:
            lines.append(f"        {item.name} = serializers.CharField(required=False, allow_blank=True)")
    return lines


def _render_class(name: str, body_lines: list[str]) -> str:
    return f"""class {name}(serializers.Serializer):\n{chr(10).join(body_lines)}\n"""


def merge_compacts_py(existing: str, ctx: gen.ScaffoldContext) -> str:
    """Create or append ``{Model}CompactSerializer`` in ``serializers/compacts.py``."""
    class_name = f"{ctx.model_name}CompactSerializer"
    class_src = _render_class(class_name, _compact_output_lines(ctx)).rstrip()

    if not existing.strip():
        return f"from rest_framework import serializers\n\n\n{class_src}\n"

    if f"class {class_name}" in existing:
        return existing if existing.endswith("\n") else existing + "\n"

    return existing.rstrip() + "\n\n\n" + class_src + "\n"


def render_resource_serializers_py(ctx: gen.ScaffoldContext) -> str:
    imports = _serializer_imports(ctx)
    compact_import = f"from .compacts import {ctx.model_name}CompactSerializer\n\n"
    create_name = f"{ctx.model_name}CreateInputSerializer"
    update_name = f"{ctx.model_name}UpdateInputSerializer"
    bulk_update_item_name = f"{ctx.model_name}BulkUpdateItemInputSerializer"
    query_name = f"{ctx.model_name}ListQuerySerializer"
    list_name = f"{ctx.model_name}ListOutputSerializer"
    detail_name = f"{ctx.model_name}DetailOutputSerializer"

    create_lines = gen._input_create_lines(ctx)
    update_lines = gen._input_update_lines(ctx)
    query_lines = gen.resource_list_query_body_lines(ctx)
    list_lines = gen._list_output_body_lines(ctx)
    detail_lines = gen._detail_output_body_lines(ctx)

    create = _render_class(create_name, create_lines)
    update = _render_class(update_name, update_lines)
    bulk_update_item = f"class {bulk_update_item_name}({update_name}):\n    id = serializers.UUIDField()\n"
    query = f"class {query_name}(ListOrderingMixin, serializers.Serializer):\n{chr(10).join(query_lines)}\n"
    list_output = _render_class(list_name, list_lines)
    detail = _render_class(detail_name, detail_lines)

    nested_helpers = gen._render_datatype_nested_helper_classes(ctx)

    parts: list[str] = [
        f"{imports}\n",
        compact_import,
        create,
        "\n\n",
        update,
        "\n\n",
        bulk_update_item,
        "\n\n",
        query,
        "\n\n",
        list_output,
        "\n\n",
        detail,
    ]
    if nested_helpers:
        parts.extend(["\n\n", nested_helpers])

    if ctx.has_history:
        m = ctx.model_name
        parts.append(
            f'\n\n\n@extend_schema_serializer(component_name="{m}HistoryDetailOutput")\n'
            f"class {m}HistoryDetailOutputSerializer({m}DetailOutputSerializer):\n"
            f'    revision = RevisionSerializer(source="*")\n'
        )

    if ctx.with_history_extras:
        m = ctx.model_name
        parts.append(
            f'\n\n@extend_schema_serializer(component_name="{m}HistoryPreviousOutput")\n'
            f"class {m}HistoryPreviousOutputSerializer({m}DetailOutputSerializer):\n"
            f'    revision = RevisionSerializer(source="*")\n'
            f'\n\n@extend_schema_serializer(component_name="{m}HistoryNextOutput")\n'
            f"class {m}HistoryNextOutputSerializer({m}DetailOutputSerializer):\n"
            f'    revision = RevisionSerializer(source="*")\n'
            f'\n\n@extend_schema_serializer(component_name="{m}HistoryRevertOutput")\n'
            f"class {m}HistoryRevertOutputSerializer({m}DetailOutputSerializer):\n"
            f'    revision = RevisionSerializer(source="*")\n'
            f'\n\n@extend_schema_serializer(component_name="{m}HistoryDiffQuery")\n'
            f"class {m}HistoryDiffQuerySerializer(serializers.Serializer):\n"
            f"    from_history_id = serializers.IntegerField()\n"
            f"    to_history_id = serializers.IntegerField()\n"
        )

    parts.append("\n")
    return "".join(parts)


def collect_generated_files(ctx: gen.ScaffoldContext, *, app_dir: Path) -> dict[Path, str]:
    return {app_dir / "serializers" / f"{ctx.resource_module}.py": render_resource_serializers_py(ctx)}


def merge_bulk_update_item_into_resource_serializers(existing: str, ctx: gen.ScaffoldContext) -> str:
    """Append ``{Model}BulkUpdateItemInputSerializer`` to an existing resource serializer file.

    No-ops when the class is already present. Raises ``ValueError`` if the
    file does not already define ``{Model}UpdateInputSerializer`` (the parent
    class).
    """

    bulk_name = f"{ctx.model_name}BulkUpdateItemInputSerializer"
    update_name = f"{ctx.model_name}UpdateInputSerializer"

    if f"class {bulk_name}" in existing:
        return existing
    if f"class {update_name}" not in existing:
        raise ValueError(
            f"serializers/{ctx.resource_module}.py does not define {update_name}; "
            "cannot append the bulk update item serializer."
        )
    block = f"class {bulk_name}({update_name}):\n    id = serializers.UUIDField()\n"
    return existing.rstrip() + "\n\n\n" + block
