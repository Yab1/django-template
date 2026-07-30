# ruff: noqa: E501
"""
Generate nine-endpoint REST scaffolding (APIs, services, selectors, filters, urls).

Used by the scaffold_standard_api management command. See docs/conventions/api_implementation.md.

Decimal conventions (keep aligned with models and ``config/settings/rest_framework.py``):

- Emit ``serializers.DecimalField`` with ``max_digits`` / ``decimal_places`` copied from the
  Django ``DecimalField`` — never ``CharField`` for decimals (including ``inline_serializer``).
- Money and most quantities: ``decimal_places=2`` on the model (generator mirrors the model).
- Geo coordinates (``longitude``, ``latitude``, ``altitude``): typically ``decimal_places=8``.
- ``coerce_to_string=False`` on every generated ``DecimalField`` (global
  ``REST_FRAMEWORK["COERCE_DECIMAL_TO_STRING"]`` is also ``False``).
"""

import importlib
import pkgutil
import re
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from django.apps import apps
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.utils.text import slugify


@dataclass
class ForeignKeySpec:
    name: str
    related_model: type[models.Model]
    required: bool


@dataclass
class ScalarFieldSpec:
    name: str
    django_field: "models.Field[Any, Any]"


@dataclass
class DependentSpec:
    """Describes a cascade-owned child model (reverse FK or OneToOne → parent)."""

    accessor: str  # related_name accessor on parent (e.g. "names", "contacts")
    child_model: type[models.Model]
    is_many: bool  # True = FK (many children), False = OneToOneField (single child)
    parent_fk_name: str  # field name on child that points back to parent
    datatype_base: str | None  # e.g. "HumanName" → use HumanName* serializers
    is_reference_domain_resource: bool  # True → parent uses *CompactSerializer + no nested writes
    child_fks: list[ForeignKeySpec]  # FK fields on child (excl. parent FK + audit FKs)
    child_m2m: list[ForeignKeySpec]  # M2M fields on child (Concept only)
    child_scalars: list[ScalarFieldSpec]  # concrete (non-mixin) scalar fields on child
    children: list["DependentSpec"]  # sub-dependents (recursive)


# Root package for shared FHIR data-type serializers. Every leaf module inside this
# package contributes any ``{Name}{Create|Output|Update}Serializer`` trio it defines to
# the discovered datatype maps below — no hardcoding, no per-type registration.
_DATATYPE_SERIALIZERS_PACKAGE = "core.common.data_types.serializers"


def _discover_datatype_serializer_maps() -> tuple[dict[str, tuple[str, str, str]], dict[str, str]]:
    """Walk ``core.common.data_types.serializers`` and harvest every datatype trio.

    For each leaf module that defines all three of ``{Name}OutputSerializer``,
    ``{Name}CreateSerializer``, and ``{Name}UpdateSerializer``, record:

      - ``serializers_map[Name] = (output, create, update)`` — the serializer class names.
      - ``module_map[Name] = "<leaf module dotted path>"`` — used to emit per-symbol
        ``from <module> import <serializer>`` lines in generated files.

    A trio split across multiple modules is rejected (defensively). Adding a new
    datatype is purely a file-create operation; no edits to this generator are needed.
    """
    serializers_map: dict[str, tuple[str, str, str]] = {}
    module_map: dict[str, str] = {}

    try:
        pkg = importlib.import_module(_DATATYPE_SERIALIZERS_PACKAGE)
    except ImportError:
        return serializers_map, module_map

    pkg_path = getattr(pkg, "__path__", None)
    if pkg_path is None:
        return serializers_map, module_map

    for info in pkgutil.walk_packages(pkg_path, prefix=f"{pkg.__name__}."):
        if info.ispkg:
            continue
        try:
            module = importlib.import_module(info.name)
        except ImportError:
            continue

        triples: dict[str, dict[str, str]] = {}
        for attr in vars(module):
            for kind, suffix in (
                ("output", "OutputSerializer"),
                ("create", "CreateSerializer"),
                ("update", "UpdateSerializer"),
            ):
                if attr.endswith(suffix) and len(attr) > len(suffix):
                    base = attr[: -len(suffix)]
                    triples.setdefault(base, {})[kind] = attr
                    break

        for base, kinds in triples.items():
            if {"output", "create", "update"}.issubset(kinds.keys()) and base not in serializers_map:
                serializers_map[base] = (kinds["output"], kinds["create"], kinds["update"])
                module_map[base] = info.name

    return serializers_map, module_map


# Discovered once at module load. Both dicts are read-only after this point; tests can
# inspect them directly and the generator never mutates them.
DATATYPE_ABSTRACT_TO_SERIALIZERS, DATATYPE_MODULE_MAP = _discover_datatype_serializer_maps()


# FHIR-style wire-format aliases for nested datatype sub-children (only used inside
# inline_serializer blocks). The accessor on the model (e.g. ``patient_human_name``) is
# replaced with the friendlier JSON key (``name`` / ``names``). Unknown types fall back
# to ``sub.accessor`` so this map is purely additive — never required.
DATATYPE_API_ALIAS_MANY: dict[str, str] = {
    "HumanName": "names",
    "Identifier": "identifiers",
    "Address": "addresses",
    "ContactPoint": "contact_points",
}
DATATYPE_API_ALIAS_ONE: dict[str, str] = {
    "HumanName": "name",
    "Identifier": "identifier",
    "Address": "address",
    "ContactPoint": "contact_point",
}


def _dep_datatype_sub_api_key(sub: DependentSpec) -> str:
    """
    Wire-format key for a datatype sub-dependent (create/update input and service pop).

    Matches output serializers: friendly names + source= on read; same keys on write.
    """
    if sub.datatype_base is None:
        return sub.accessor
    if sub.is_many:
        return DATATYPE_API_ALIAS_MANY.get(sub.datatype_base, sub.accessor)
    return DATATYPE_API_ALIAS_ONE.get(sub.datatype_base, sub.accessor)


def _child_has_own_apis_module(child_model: type[models.Model]) -> bool:
    """True if ``child_model`` has its own scaffolded ``core.<app>.apis.<snake>`` package.

    Convention-based, model-driven detection of a "reference domain resource":
    every scaffolded REST resource produces ``core/<app>/apis/<snake>/`` (with
    ``crud.py``, ``history.py``, ``audit.py``, ``__init__.py``). Cascade children
    that have this package are first-class resources and should be referenced from
    parent serializers via ``{Model}CompactSerializer`` (imported blindly from
    ``core.<app>.serializers.<snake>``) — never inlined and never wired into the
    parent service's nested-child helpers (clients use the child resource APIs).

    True inline children (e.g. ``PatientCommunication``, ``PatientContact``,
    ``PractitionerQualification``) have no ``apis/<snake>`` package and continue
    to be rendered inline.
    """
    module_name = child_model.__module__
    if ".models" not in module_name:
        return False
    app_path = module_name.split(".models", 1)[0]
    snake = _entity_snake(child_model.__name__)

    # Resolve the app's on-disk directory from its top-level package, then probe the
    # filesystem for ``apis/<snake>/__init__.py`` or ``apis/<snake>.py``. We deliberately
    # avoid ``importlib.import_module`` / ``find_spec`` because both transitively execute
    # the parent ``apis/__init__.py`` — and an unrelated downstream ImportError inside
    # any sibling apis package (e.g. a stale symbol name still being imported) would
    # otherwise masquerade as "this package doesn't exist" and silently flip a reference
    # domain resource back into an inlined dependent.
    try:
        app_pkg = importlib.import_module(app_path)
    except ImportError:
        return False
    app_file = getattr(app_pkg, "__file__", None)
    if app_file is None:
        return False
    app_dir = Path(app_file).resolve().parent
    apis_dir = app_dir / "apis"
    if (apis_dir / snake / "__init__.py").is_file():
        return True
    if (apis_dir / f"{snake}.py").is_file():
        return True
    return False


# Fields to skip when collecting child-model fields for DependentSpec.
_DEP_SKIP_FIELD_NAMES = frozenset({"id", "created_at", "updated_at", "deleted_at", "deleted_by"})

# Dependent child models: include mixin fields (``metadata``, ``is_visible``, timestamps, soft-delete
# columns) in serializers. Only skip PK and the simple-history ``history`` relation (not a serializable
# column).
_DEP_CHILD_FIELD_SKIP = frozenset({"id", "history"})

# Concrete dependent inline_serializer: domain fields first, then sub-children, then this tail (only if present).
_DEP_INLINE_CONVENTION_TAIL_ORDER: tuple[str, ...] = (
    "is_visible",
    "is_deleted",
    "deleted_at",
    "deleted_by",
    "created_at",
    "updated_at",
    "metadata",
)
_DEP_INLINE_TAIL_SCALAR_NAMES = frozenset({"is_visible", "deleted_at", "created_at", "updated_at", "metadata"})
# Subset of the tail that the client is allowed to write; server-managed fields are excluded from all inputs.
_DEP_INPUT_WRITABLE_TAIL = frozenset({"is_visible", "metadata"})


def _drf_decimal_field_expr(
    field: models.DecimalField,
    *,
    extra_parts: tuple[str, ...] = (),
) -> str:
    """DRF ``DecimalField`` expression mirroring a Django ``DecimalField`` (never ``CharField``)."""
    parts = [
        f"max_digits={field.max_digits}",
        f"decimal_places={field.decimal_places}",
        "coerce_to_string=False",
        *extra_parts,
    ]
    return f"serializers.DecimalField({', '.join(parts)})"


def _fk_related_is_terminology_concept(fk: ForeignKeySpec) -> bool:
    """Reserved hook — template has no terminology.Concept; always False."""
    del fk
    return False


def _fk_related_is_content_type(fk: ForeignKeySpec) -> bool:
    m = fk.related_model
    return m.__name__ == "ContentType" and m._meta.app_label == "contenttypes"


def _fk_related_is_user(fk: ForeignKeySpec) -> bool:
    m = fk.related_model
    return m.__name__ == "User"


def _context_has_terminology_concept_fk(ctx: "ScaffoldContext") -> bool:
    return any(_fk_related_is_terminology_concept(fk) for fk in ctx.foreign_keys)


def _context_has_content_type_fk(ctx: "ScaffoldContext") -> bool:
    return any(_fk_related_is_content_type(fk) for fk in ctx.foreign_keys)


@dataclass
class ScaffoldContext:
    app_label: str
    # Lowercase label for URL includes and app_name (matches core/api/urls.py style).
    app_url_namespace: str
    app_python_path: str
    model: type[models.Model]
    model_name: str
    resource_module: str
    url_prefix: str
    openapi_tag_constant_name: str
    openapi_tag_value: str
    filter_class_name: str
    has_visible: bool
    has_soft_delete: bool
    has_history: bool
    historical_model_name: str
    foreign_keys: list[ForeignKeySpec] = field(default_factory=list)
    scalar_fields: list[ScalarFieldSpec] = field(default_factory=list)
    # Concrete model fields first (declaration order), then mixin/base fields. Excludes reference_id.
    ordered_fields: list[ForeignKeySpec | ScalarFieldSpec] = field(default_factory=list)
    # From ReferenceIdMixin; emitted in serializers immediately after ``id``.
    reference_id_field: ScalarFieldSpec | None = None
    fk_imports: list[tuple[str, str]] = field(default_factory=list)
    update_field_names: list[str] = field(default_factory=list)
    # Root M2M fields (e.g. Practitioner.communication → Concept).
    m2m_fields: list[ForeignKeySpec] = field(default_factory=list)
    # Cascade-owned child models discovered at build time.
    dependents: list[DependentSpec] = field(default_factory=list)
    # Optional blocks (see docs/conventions/api_implementation.md — extended blueprint).
    with_history_extras: bool = True
    with_crud_audit: bool = True
    rich_serializers: bool = False
    # Whether a filter class was generated (False when --skip-filters is used).
    with_filters: bool = True


SKIP_CREATE_NAMES = frozenset({"id", "created_at", "updated_at", "deleted_at", "deleted_by"})
SKIP_UPDATE_NAMES = frozenset({"id", "created_at", "updated_at", "deleted_at", "deleted_by"})


def _related_model_class(fk: models.ForeignKey[Any, Any]) -> type[models.Model]:
    rel = fk.remote_field.model
    if isinstance(rel, str):
        return apps.get_model(rel)
    return rel


def _top_pkg(module: str) -> str:
    """Normalize a deep submodule path to its top-level package boundary.

    The convention in this codebase is that every layer (models, services,
    selectors, apis) has a barrel ``__init__.py`` that re-exports everything.
    So we always import from ``core.<app>.models`` rather than
    ``core.<app>.models.location.address``.

    The rule: truncate at the first segment that equals one of the known
    boundary keywords.  For third-party paths (django, easyaudit, …) the
    module is returned unchanged because their subpackage is already the
    canonical import.
    """
    _BOUNDARIES = {"models", "services", "selectors", "apis", "serializers", "filters"}  # noqa: N806
    parts = module.split(".")
    for i, part in enumerate(parts):
        if part in _BOUNDARIES:
            return ".".join(parts[: i + 1])
    return module


def _collect_fk_imports(fks: list[ForeignKeySpec]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for fk in fks:
        m = fk.related_model
        key = (_top_pkg(m.__module__), m.__name__)
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def _get_datatype_base(model: type[models.Model]) -> str | None:
    """Return the FHIR data-type abstract base name (e.g. 'HumanName') if ``model`` inherits it."""
    for cls in model.__mro__:
        if cls.__name__ in DATATYPE_ABSTRACT_TO_SERIALIZERS:
            meta = getattr(cls, "_meta", None)
            if meta and getattr(meta, "abstract", False):
                return cls.__name__
    return None


def _discover_dependents(
    model: type[models.Model],
    *,
    depth: int = 0,
    max_depth: int = 2,
) -> list[DependentSpec]:
    """
    Walk ``model._meta.related_objects`` and return cascade-owned child DependentSpecs.

    Only FK and O2O relations with ``on_delete=CASCADE`` are included.
    Historical models and M2M are skipped.
    Recursion stops at ``max_depth``.
    """
    if depth >= max_depth:
        return []
    result: list[DependentSpec] = []
    for rel in model._meta.related_objects:
        if rel.many_to_many:
            continue
        if getattr(rel, "on_delete", None) is not models.CASCADE:
            continue
        accessor = rel.get_accessor_name()
        if not accessor:
            continue
        child_model: type[models.Model] = rel.related_model
        if child_model.__name__.startswith("Historical"):
            continue
        is_many = not rel.one_to_one
        parent_fk_name: str = rel.field.name

        child_fks: list[ForeignKeySpec] = []
        child_m2m: list[ForeignKeySpec] = []
        child_scalars: list[ScalarFieldSpec] = []
        for f in child_model._meta.local_fields:
            if f.name in _DEP_CHILD_FIELD_SKIP:
                continue
            if f.primary_key:
                continue
            if f.name == parent_fk_name:
                continue
            if isinstance(f, models.OneToOneField):
                continue
            if isinstance(f, models.ForeignKey):
                child_fks.append(
                    ForeignKeySpec(
                        name=f.name,
                        related_model=_related_model_class(f),
                        required=not f.null,
                    )
                )
            elif not isinstance(f, (models.ManyToManyField, models.AutoField)):
                # Include mixin/base scalars (``metadata``, ``is_visible``, ``deleted_at``, …).
                child_scalars.append(ScalarFieldSpec(name=f.name, django_field=f))
        # Collect M2M fields (typically Concept FK sets like `relationship`)
        for f in child_model._meta.local_many_to_many:
            related = _related_model_class(f)  # type: ignore[arg-type]
            child_m2m.append(ForeignKeySpec(name=f.name, related_model=related, required=False))

        sub_children = _discover_dependents(child_model, depth=depth + 1, max_depth=max_depth)
        datatype_base = _get_datatype_base(child_model)
        is_reference_domain_resource = datatype_base is None and _child_has_own_apis_module(child_model)

        result.append(
            DependentSpec(
                accessor=accessor,
                child_model=child_model,
                is_many=is_many,
                parent_fk_name=parent_fk_name,
                datatype_base=datatype_base,
                is_reference_domain_resource=is_reference_domain_resource,
                child_fks=child_fks,
                child_m2m=child_m2m,
                child_scalars=child_scalars,
                children=sub_children,
            )
        )
    return result


def _all_dep_output_serializer_names(dependents: list[DependentSpec]) -> set[str]:
    """Collect Output serializer class names needed for the dep tree."""
    names: set[str] = set()
    for dep in dependents:
        if dep.is_reference_domain_resource:
            continue
        if dep.datatype_base:
            names.add(DATATYPE_ABSTRACT_TO_SERIALIZERS[dep.datatype_base][0])
        names.update(_all_dep_output_serializer_names(dep.children))
    return names


def _all_dep_input_serializer_names(dependents: list[DependentSpec]) -> set[str]:
    """Collect Create + Update serializer class names needed for the dep tree."""
    names: set[str] = set()
    for dep in dependents:
        if dep.is_reference_domain_resource:
            continue
        if dep.datatype_base:
            names.add(DATATYPE_ABSTRACT_TO_SERIALIZERS[dep.datatype_base][1])
            names.add(DATATYPE_ABSTRACT_TO_SERIALIZERS[dep.datatype_base][2])
        names.update(_all_dep_input_serializer_names(dep.children))
    return names


def _any_dep_has_concept_fk(dependents: list[DependentSpec]) -> bool:
    """True if any (recursive) dependent has a terminology Concept FK or M2M."""
    for dep in dependents:
        for fk in dep.child_fks + dep.child_m2m:
            if _fk_related_is_terminology_concept(fk):
                return True
        if dep.is_reference_domain_resource:
            continue
        if _any_dep_has_concept_fk(dep.children):
            return True
    return False


def _any_dep_has_user_fk(dependents: list[DependentSpec]) -> bool:
    """True if any (recursive) dependent has an FK to User (e.g. ``deleted_by``)."""
    for dep in dependents:
        for fk in dep.child_fks:
            if _fk_related_is_user(fk):
                return True
        if dep.is_reference_domain_resource:
            continue
        if _any_dep_has_user_fk(dep.children):
            return True
    return False


def _any_dep_has_content_type_fk(dependents: list[DependentSpec]) -> bool:
    """True if any (recursive) dependent has an FK to ContentType."""
    for dep in dependents:
        for fk in dep.child_fks:
            if _fk_related_is_content_type(fk):
                return True
        if dep.is_reference_domain_resource:
            continue
        if _any_dep_has_content_type_fk(dep.children):
            return True
    return False


_EXTENSION_VALUE_OUTPUT_SERIALIZER = "ExtensionFieldValueOutputSerializer"
_EXTENSION_VALUE_CREATE_INPUT_SERIALIZER = "ExtensionFieldValueCreateInputSerializer"
_EXTENSION_VALUE_UPDATE_INPUT_SERIALIZER = "ExtensionFieldValueUpdateInputSerializer"


def _is_extension_values_dependent(dep: DependentSpec) -> bool:
    """Reserved hook — template has no extensions app; always False."""
    del dep
    return False


def _any_dep_uses_extension_field_compact(dependents: list[DependentSpec]) -> bool:
    del dependents
    return False


def _is_required_for_create(django_field: "models.Field[Any, Any]") -> bool:
    if django_field.primary_key:
        return False
    if getattr(django_field, "auto_now", False) or getattr(django_field, "auto_now_add", False):
        return False
    if django_field.name in SKIP_CREATE_NAMES:
        return False
    if django_field.has_default():
        return False
    if getattr(django_field, "blank", False):
        return False
    if getattr(django_field, "null", False):
        return False
    return True


def _model_has_field(model: type[models.Model], name: str) -> bool:
    try:
        model._meta.get_field(name)
        return True
    except FieldDoesNotExist:
        return False


def _datatype_dep_extra_scalars(dep: DependentSpec) -> list[ScalarFieldSpec]:
    """
    Scalars declared on the concrete child model but not on any abstract ancestor
    (e.g. ``ScheduleAvailableTime.slot_minutes_duration`` on top of ``AvailableTime``).
    """
    if not dep.datatype_base:
        return []
    abstract_names = _field_names_from_abstract_ancestors(dep.child_model)
    return [sc for sc in dep.child_scalars if sc.name not in abstract_names]


def _serializer_class_scalar_input_line(sc: ScalarFieldSpec, model: type[models.Model]) -> str:
    return f"    {sc.name} = {_inline_scalar_input_str(sc, model=model)}"


def _serializer_class_scalar_output_line(sc: ScalarFieldSpec, model: type[models.Model]) -> str:
    line = _inline_scalar_output_str(sc, model=model, dict_key=False)
    return "    " + line.lstrip()


def _render_datatype_nested_helper_classes(ctx: ScaffoldContext) -> str:
    """Emit ``{ConcreteChild}Nested{Output,Create,Update}Serializer`` subclasses when a datatype dependent adds fields."""
    blocks: list[str] = []
    seen_models: set[str] = set()
    for dep in ctx.dependents:
        extras = _datatype_dep_extra_scalars(dep)
        if not dep.datatype_base or not extras:
            continue
        cls_base = dep.child_model.__name__
        if cls_base in seen_models:
            continue
        seen_models.add(cls_base)
        out_name, create_name, update_name = DATATYPE_ABSTRACT_TO_SERIALIZERS[dep.datatype_base]
        out_body = "\n".join(_serializer_class_scalar_output_line(sc, dep.child_model) for sc in extras)
        in_body = "\n".join(_serializer_class_scalar_input_line(sc, dep.child_model) for sc in extras)
        blocks.append(
            "\n".join([
                f"class {cls_base}NestedOutputSerializer({out_name}):",
                out_body,
                "",
                f"class {cls_base}NestedCreateSerializer({create_name}):",
                in_body,
                "",
                f"class {cls_base}NestedUpdateSerializer({update_name}):",
                in_body,
                "",
            ])
        )
    return "\n".join(blocks).rstrip()


def _field_names_from_abstract_ancestors(model: type[models.Model]) -> set[str]:
    """
    Names of non-PK fields contributed by **abstract** ancestor models in the MRO.

    Django copies inherited fields onto the concrete model and sets ``Field.model`` to the
    concrete class, so ``get_field(...).model == model`` is true for *all* local fields.
    We must use abstract bases to tell mixin/base fields (e.g. ``metadata``, ``is_visible``)
    from fields declared on the concrete class.
    """
    names: set[str] = set()
    for cls in model.__mro__[1:]:
        if cls in (object, models.Model):
            break
        meta = getattr(cls, "_meta", None)
        if meta is None:
            continue
        if not getattr(meta, "abstract", False):
            continue
        for f in meta.local_fields:
            if f.primary_key:
                continue
            names.add(f.name)
    return names


def _partition_field_order(
    model: type[models.Model],
    raw: list[ForeignKeySpec | ScalarFieldSpec],
) -> tuple[ScalarFieldSpec | None, list[ForeignKeySpec | ScalarFieldSpec]]:
    """
    Order: concrete model fields first, then fields inherited from abstract bases / mixins.
    ``reference_id`` (ReferenceIdMixin) is pulled out for placement next to ``id`` in APIs.
    """
    reference_id_field: ScalarFieldSpec | None = None
    rest: list[ForeignKeySpec | ScalarFieldSpec] = []
    for spec in raw:
        if isinstance(spec, ScalarFieldSpec) and spec.name == "reference_id":
            reference_id_field = spec
            continue
        rest.append(spec)
    abstract_field_names = _field_names_from_abstract_ancestors(model)
    concrete: list[ForeignKeySpec | ScalarFieldSpec] = []
    inherited: list[ForeignKeySpec | ScalarFieldSpec] = []
    for spec in rest:
        if spec.name in abstract_field_names:
            inherited.append(spec)
        else:
            concrete.append(spec)
    return reference_id_field, concrete + inherited


def _service_ordered_field_items(ctx: ScaffoldContext) -> list[ForeignKeySpec | ScalarFieldSpec]:
    """Create/update/revert writable field loops (reference_id is intentionally excluded)."""
    return list(ctx.ordered_fields)


def _iter_scalar_specs_for_choices(ctx: ScaffoldContext):
    if ctx.reference_id_field is not None:
        yield ctx.reference_id_field
    for item in ctx.ordered_fields:
        if isinstance(item, ScalarFieldSpec):
            yield item


def _default_url_prefix(model: type[models.Model]) -> str:
    raw = str(model._meta.verbose_name_plural or model._meta.verbose_name or model.__name__)
    slug = slugify(raw)
    if not slug:
        slug = slugify(model._meta.model_name.replace("_", "-")) + "s"
    return slug


def build_context(
    *,
    model: type[models.Model],
    url_prefix: str | None,
    openapi_tag: str | None,
    with_history_extras: bool = True,
    with_crud_audit: bool = True,
    rich_serializers: bool = False,
    with_filters: bool = True,
) -> ScaffoldContext:
    if not isinstance(model._meta.pk, models.UUIDField):
        raise ValueError(
            "scaffold_standard_api only supports models whose primary key is a UUIDField (e.g. BaseModel)."
        )

    app_config = apps.get_app_config(model._meta.app_label)
    app_python_path = app_config.name
    app_url_namespace = model._meta.app_label.lower()

    resource_module = _entity_snake(model.__name__)
    prefix = (url_prefix or _default_url_prefix(model)).strip().strip("/")
    # Default tag value matches the resource slug only (e.g. "diagnostic-reports").
    default_openapi_tag_value = prefix
    tag_value = openapi_tag.strip() if openapi_tag is not None and openapi_tag.strip() else default_openapi_tag_value
    tag_suffix = prefix.replace("-", "_").upper()
    tag_constant = f"OPENAPI_TAG_{model._meta.app_label.upper()}_{tag_suffix}"

    has_visible = _model_has_field(model, "is_visible")
    has_soft_delete = _model_has_field(model, "deleted_at")
    has_history = False
    historical_model_name = f"Historical{model.__name__}"
    try:
        apps.get_model(model._meta.app_label, historical_model_name)
        has_history = True
    except LookupError:
        pass

    # django-simple-history registers Historical* only after HistoryMixin + migrations; scaffold
    # skips history endpoints/selectors/services when it is missing (same idea for soft-delete).
    with_history_extras = bool(with_history_extras and has_history)

    foreign_keys: list[ForeignKeySpec] = []
    scalar_fields: list[ScalarFieldSpec] = []
    raw_ordered: list[ForeignKeySpec | ScalarFieldSpec] = []

    for django_field in model._meta.local_fields:
        if django_field.name in SKIP_UPDATE_NAMES:
            continue
        if django_field.primary_key:
            continue
        if isinstance(django_field, models.OneToOneField):
            continue
        if isinstance(django_field, models.ForeignKey):
            fk_spec = ForeignKeySpec(
                name=django_field.name,
                related_model=_related_model_class(django_field),
                required=not django_field.null,
            )
            foreign_keys.append(fk_spec)
            raw_ordered.append(fk_spec)
        elif not isinstance(
            django_field,
            (models.ManyToManyField, models.OneToOneField),
        ):
            # OneToOne as local field is rare for our pattern; skip if it's the reverse side only
            if isinstance(django_field, models.AutoField):
                continue
            sc_spec = ScalarFieldSpec(name=django_field.name, django_field=django_field)
            scalar_fields.append(sc_spec)
            raw_ordered.append(sc_spec)

    reference_id_field, ordered_fields = _partition_field_order(model, raw_ordered)

    update_field_names = [f.name for f in ordered_fields]

    fk_imports = _collect_fk_imports(foreign_keys)
    dependents = _discover_dependents(model)

    m2m_fields: list[ForeignKeySpec] = []
    for m2m_field in model._meta.local_many_to_many:
        related = _related_model_class(m2m_field)
        m2m_fields.append(ForeignKeySpec(name=m2m_field.name, related_model=related, required=False))

    return ScaffoldContext(
        app_label=model._meta.app_label,
        app_url_namespace=app_url_namespace,
        app_python_path=app_python_path,
        model=model,
        model_name=model.__name__,
        resource_module=resource_module,
        url_prefix=prefix,
        openapi_tag_constant_name=tag_constant,
        openapi_tag_value=tag_value,
        filter_class_name=f"{model.__name__}Filter",
        has_visible=has_visible,
        has_soft_delete=has_soft_delete,
        has_history=has_history,
        historical_model_name=historical_model_name,
        foreign_keys=foreign_keys,
        scalar_fields=scalar_fields,
        ordered_fields=ordered_fields,
        reference_id_field=reference_id_field,
        fk_imports=fk_imports,
        update_field_names=update_field_names,
        m2m_fields=m2m_fields,
        dependents=dependents,
        with_history_extras=with_history_extras,
        with_crud_audit=with_crud_audit,
        rich_serializers=rich_serializers,
        with_filters=with_filters,
    )


def _django_field_has_flat_choices(f: "models.Field[Any, Any]") -> bool:
    try:
        return len(list(f.flatchoices)) > 0
    except (TypeError, AttributeError, ValueError):
        return False


def _choices_literal_python(f: "models.Field[Any, Any]") -> str | None:
    """Stable ``choices=`` argument for DRF ``ChoiceField`` (from model at scaffold time)."""
    try:
        flat = list(f.flatchoices)
    except (TypeError, AttributeError, ValueError):
        return None
    if not flat:
        return None
    return repr(flat)


def _find_choices_enum_descriptor(
    model: type[models.Model], field: "models.Field[Any, Any]"
) -> tuple[type, str] | None:
    """
    If ``field.choices`` matches a nested ``models.Choices`` subclass on the model MRO,
    return ``(class_that_defines_the_enum, attribute_name)`` for
    ``Parent.MembershipMode.choices``-style output.
    """
    try:
        field_choices = list(field.choices)
    except (TypeError, AttributeError, ValueError):
        return None
    if not field_choices:
        return None

    for cls in model.__mro__:
        if cls is object:
            continue
        for attr_name in dir(cls):
            if attr_name.startswith("_"):
                continue
            nested = getattr(cls, attr_name, None)
            if not isinstance(nested, type):
                continue
            try:
                if not issubclass(nested, models.Choices):
                    continue
            except TypeError:
                continue
            try:
                if list(nested.choices) == field_choices:
                    return (cls, attr_name)
            except (TypeError, AttributeError, ValueError):
                continue
    return None


def _postgres_array_innermost_scalar(field: "models.Field[Any, Any]") -> "models.Field[Any, Any]":
    cur: "models.Field[Any, Any]" = field
    while isinstance(cur, ArrayField):
        cur = cur.base_field
    return cur


def _choice_field_choices_argument(model: type[models.Model], django_field: "models.Field[Any, Any]") -> str | None:
    f = django_field
    if not _django_field_has_flat_choices(f):
        return None
    desc = _find_choices_enum_descriptor(model, f)
    if desc is not None:
        parent_cls, attr_name = desc
        return f"{parent_cls.__name__}.{attr_name}.choices"
    return _choices_literal_python(f)


def _postgres_array_to_listfield_child_expr(model: type[models.Model], base_field: "models.Field[Any, Any]") -> str:
    if isinstance(base_field, ArrayField):
        inner = _postgres_array_to_listfield_child_expr(model, base_field.base_field)
        return f"serializers.ListField(child={inner})"
    arg = _choice_field_choices_argument(model, base_field)
    if arg is not None:
        return f"serializers.ChoiceField(choices={arg})"
    if isinstance(base_field, models.BooleanField):
        return "serializers.BooleanField()"
    if isinstance(base_field, models.IntegerField):
        return "serializers.IntegerField()"
    if isinstance(base_field, models.UUIDField):
        return "serializers.UUIDField()"
    if isinstance(base_field, models.DecimalField):
        return _drf_decimal_field_expr(base_field)
    if isinstance(base_field, models.FloatField):
        return "serializers.FloatField()"
    if isinstance(base_field, models.URLField):
        return "serializers.URLField()"
    if isinstance(base_field, models.EmailField):
        return "serializers.EmailField()"
    if isinstance(base_field, (models.TextField, models.CharField)):
        return "serializers.CharField()"
    return "serializers.CharField()"


def _postgres_array_python_type_annotation(field: ArrayField) -> str:
    base = field.base_field
    if isinstance(base, ArrayField):
        return f"list[{_postgres_array_python_type_annotation(base)}]"
    if isinstance(base, models.UUIDField):
        return "list[UUID]"
    if isinstance(base, models.IntegerField):
        return "list[int]"
    if isinstance(base, models.BooleanField):
        return "list[bool]"
    return "list[str]"


def _collect_unique_choices_parent_classes(ctx: ScaffoldContext) -> list[type]:
    seen: set[type] = set()
    out: list[type] = []
    for item in _iter_scalar_specs_for_choices(ctx):
        f = item.django_field
        inspect_f = _postgres_array_innermost_scalar(f) if isinstance(f, ArrayField) else f
        if not _django_field_has_flat_choices(inspect_f):
            continue
        desc = _find_choices_enum_descriptor(ctx.model, inspect_f)
        if desc is None:
            continue
        parent_cls, _ = desc
        if parent_cls not in seen:
            seen.add(parent_cls)
            out.append(parent_cls)
    return out


def _import_line_for_choices_parent_class(ctx: ScaffoldContext, parent_cls: type) -> str:
    mod = _top_pkg(parent_cls.__module__)
    name = parent_cls.__name__
    return f"from {mod} import {name}"


def _apis_choice_enum_imports(ctx: ScaffoldContext) -> str:
    parents = _collect_unique_choices_parent_classes(ctx)
    if not parents:
        return ""
    lines = sorted({_import_line_for_choices_parent_class(ctx, p) for p in parents})
    return "\n".join(lines) + "\n\n"


def _drf_output_line_scalar(ctx: ScaffoldContext, spec: ScalarFieldSpec) -> str:
    f = spec.django_field
    name = spec.name
    if isinstance(f, ArrayField):
        child = _postgres_array_to_listfield_child_expr(ctx.model, f.base_field)
        return f"        {name} = serializers.ListField(child={child}, required=False, allow_empty=True)"
    arg = _choice_field_choices_argument(ctx.model, f)
    if arg is not None:
        return f"        {name} = serializers.ChoiceField(choices={arg})"
    if isinstance(f, models.BooleanField):
        return f"        {name} = serializers.BooleanField()"
    if isinstance(f, models.IntegerField):
        return f"        {name} = serializers.IntegerField()"
    if isinstance(f, models.UUIDField):
        return f"        {name} = serializers.UUIDField()"
    if isinstance(f, models.DateTimeField):
        return f"        {name} = serializers.DateTimeField(required=False, allow_null=True)"
    if isinstance(f, models.DateField):
        return f"        {name} = serializers.DateField(required=False, allow_null=True)"
    if isinstance(f, models.TimeField):
        return f"        {name} = serializers.TimeField(required=False, allow_null=True)"
    if isinstance(f, models.DecimalField):
        return f"        {name} = {_drf_decimal_field_expr(f)}"
    if isinstance(f, models.FloatField):
        return f"        {name} = serializers.FloatField()"
    if isinstance(f, models.JSONField):
        return f"        {name} = serializers.JSONField(required=False)"
    if isinstance(f, models.URLField):
        return f"        {name} = serializers.URLField(required=False, allow_blank=True)"
    if isinstance(f, models.EmailField):
        return f"        {name} = serializers.EmailField(required=False, allow_blank=True)"
    if isinstance(f, (models.TextField, models.CharField)):
        return f"        {name} = serializers.CharField(required=False, allow_blank=True)"
    return f"        # TODO: map Django field {type(f).__name__} for {name}"


def _drf_input_line_scalar_create(ctx: ScaffoldContext, spec: ScalarFieldSpec) -> str | None:
    f = spec.django_field
    name = spec.name
    if getattr(f, "auto_now", False) or getattr(f, "auto_now_add", False):
        return None
    req = _is_required_for_create(f)
    if isinstance(f, ArrayField):
        child = _postgres_array_to_listfield_child_expr(ctx.model, f.base_field)
        if req:
            return f"        {name} = serializers.ListField(child={child}, allow_empty=True)"
        return (
            f"        {name} = serializers.ListField(child={child}, required=False, allow_empty=True, allow_null=True)"
        )
    arg = _choice_field_choices_argument(ctx.model, f)
    if arg is not None:
        inner = f"choices={arg}, required={req}"
        if not req:
            inner += ", allow_null=True"
        return f"        {name} = serializers.ChoiceField({inner})"
    if isinstance(f, models.BooleanField):
        extra = "" if req else "required=False, "
        return f"        {name} = serializers.BooleanField({extra})".replace(", )", ")")
    if isinstance(f, models.IntegerField):
        inner = f"required={req}"
        if not req:
            inner += ", allow_null=True"
        return f"        {name} = serializers.IntegerField({inner})"
    if isinstance(f, models.UUIDField):
        return f"        {name} = serializers.UUIDField({'' if req else 'required=False, allow_null=True'})"
    if isinstance(f, models.DateTimeField):
        inner = f"required={req}"
        if not req:
            inner += ", allow_null=True"
        return f"        {name} = serializers.DateTimeField({inner})"
    if isinstance(f, models.DateField):
        inner = f"required={req}"
        if not req:
            inner += ", allow_null=True"
        return f"        {name} = serializers.DateField({inner})"
    if isinstance(f, models.TimeField):
        inner = f"required={req}"
        if not req:
            inner += ", allow_null=True"
        return f"        {name} = serializers.TimeField({inner})"
    if isinstance(f, models.DecimalField):
        extra: list[str] = [f"required={req}"]
        if not req:
            extra.append("allow_null=True")
        return f"        {name} = {_drf_decimal_field_expr(f, extra_parts=tuple(extra))}"
    if isinstance(f, models.FloatField):
        inner = f"required={req}"
        if not req:
            inner += ", allow_null=True"
        return f"        {name} = serializers.FloatField({inner})"
    if isinstance(f, models.JSONField):
        return f"        {name} = serializers.JSONField(required=False)"
    if isinstance(f, models.URLField):
        inner = "required=False, allow_blank=True" if not req else ""
        return f"        {name} = serializers.URLField({inner})".replace("()", "()")
    if isinstance(f, models.EmailField):
        inner = "required=False, allow_blank=True" if not req else ""
        return f"        {name} = serializers.EmailField({inner})".strip()
    if isinstance(f, (models.TextField, models.CharField)):
        inner = "" if req else "required=False, allow_blank=True"
        return f"        {name} = serializers.CharField({inner})".replace("()", "()")
    return f"        # TODO: input for {name} ({type(f).__name__})"


def _drf_input_line_fk_create(fk: ForeignKeySpec) -> str:
    if _fk_related_is_content_type(fk):
        if fk.required:
            return f'        {fk.name} = ContentTypeNaturalKeyField(source="{fk.name}_id")'
        return f'        {fk.name} = ContentTypeNaturalKeyField(source="{fk.name}_id", required=False, allow_null=True)'
    if fk.required:
        return f"        {fk.name}_id = serializers.UUIDField()"
    return f"        {fk.name}_id = serializers.UUIDField(required=False, allow_null=True)"


def _drf_input_line_fk_update(fk: ForeignKeySpec) -> str:
    if _fk_related_is_content_type(fk):
        return f'        {fk.name} = ContentTypeNaturalKeyField(source="{fk.name}_id", required=False, allow_null=True)'
    return f"        {fk.name}_id = serializers.UUIDField(required=False, allow_null=True)"


def _drf_output_line_fk(fk: ForeignKeySpec) -> str:
    if _fk_related_is_terminology_concept(fk):
        if fk.required:
            return f"        {fk.name} = ConceptCompactSerializer()"
        return f"        {fk.name} = ConceptCompactSerializer(required=False, allow_null=True)"
    if _fk_related_is_content_type(fk):
        if fk.required:
            return f"        {fk.name} = ContentTypeCompactSerializer()"
        return f"        {fk.name} = ContentTypeCompactSerializer(required=False, allow_null=True)"
    rel_name = fk.related_model.__name__
    if fk.required:
        return f"        {fk.name} = {rel_name}CompactSerializer()"
    return f"        {fk.name} = {rel_name}CompactSerializer(required=False, allow_null=True)"


def _inline_scalar_output_str(
    sc: ScalarFieldSpec,
    *,
    model: type[models.Model],
    dict_key: bool = False,
    field_indent: str = "                ",
) -> str:
    """Render a scalar field as an output serializer expression for inline_serializer dicts."""
    f = sc.django_field
    nullable = getattr(f, "null", False)
    optional = " allow_null=True" if nullable else ""
    if isinstance(f, ArrayField):
        child_expr = _postgres_array_to_listfield_child_expr(model, f.base_field)
        expr = f"serializers.ListField(child={child_expr}, required=False, allow_empty=True)"
        if dict_key:
            return f'{field_indent}"{sc.name}": {expr},'
        return f"        {sc.name} = {expr}"
    if isinstance(f, models.BooleanField):
        expr = "serializers.BooleanField()"
    elif isinstance(f, models.PositiveSmallIntegerField):
        expr = f"serializers.IntegerField({optional.strip()})" if nullable else "serializers.IntegerField()"
    elif isinstance(f, models.IntegerField):
        expr = f"serializers.IntegerField({optional.strip()})" if nullable else "serializers.IntegerField()"
    elif isinstance(f, models.UUIDField):
        expr = f"serializers.UUIDField({optional.strip()})" if nullable else "serializers.UUIDField()"
    elif isinstance(f, models.DateTimeField):
        expr = "serializers.DateTimeField(allow_null=True)" if nullable else "serializers.DateTimeField()"
    elif isinstance(f, models.DateField):
        expr = "serializers.DateField(allow_null=True)" if nullable else "serializers.DateField()"
    elif isinstance(f, models.TimeField):
        expr = "serializers.TimeField(allow_null=True)" if nullable else "serializers.TimeField()"
    elif isinstance(f, models.JSONField):
        expr = "serializers.JSONField(required=False)"
    elif isinstance(f, models.DecimalField):
        extra = ("allow_null=True",) if nullable else ()
        expr = _drf_decimal_field_expr(f, extra_parts=extra)
    elif isinstance(f, models.FloatField):
        expr = f"serializers.FloatField({optional.strip()})" if nullable else "serializers.FloatField()"
    elif isinstance(f, models.URLField):
        expr = "serializers.URLField(allow_null=True)" if nullable else "serializers.URLField()"
    elif isinstance(f, (models.TextField, models.CharField)):
        expr = "serializers.CharField(allow_null=True)" if nullable else "serializers.CharField()"
    else:
        expr = "serializers.CharField(allow_null=True)"
    if dict_key:
        return f'{field_indent}"{sc.name}": {expr},'
    return f"        {sc.name} = {expr}"


def _inline_fk_output_str(fk: ForeignKeySpec, *, dict_key: bool = False, field_indent: str = "                ") -> str:
    null_arg = ", allow_null=True" if not fk.required else ""
    if _fk_related_is_terminology_concept(fk):
        expr = f"ConceptCompactSerializer({null_arg.lstrip(', ')})" if null_arg else "ConceptCompactSerializer()"
    elif _fk_related_is_user(fk):
        expr = f"UserCompactSerializer({null_arg.lstrip(', ')})" if null_arg else "UserCompactSerializer()"
    elif _fk_related_is_content_type(fk):
        expr = (
            f"ContentTypeCompactSerializer({null_arg.lstrip(', ')})" if null_arg else "ContentTypeCompactSerializer()"
        )
    else:
        expr = (
            f"{fk.related_model.__name__}CompactSerializer({null_arg.lstrip(', ')})"
            if null_arg
            else f"{fk.related_model.__name__}CompactSerializer()"
        )
    if dict_key:
        return f'{field_indent}"{fk.name}": {expr},'
    return f"        {fk.name} = {expr}"


def _concrete_dep_inline_other_fks(dep: DependentSpec) -> list[ForeignKeySpec]:
    """FKs on a concrete dependent except ``deleted_by`` (emitted in the convention tail)."""
    return [fk for fk in dep.child_fks if fk.name != "deleted_by"]


def _concrete_dep_inline_other_scalars(dep: DependentSpec) -> list[ScalarFieldSpec]:
    """Scalars not in the fixed tail block (visibility, soft-delete, audit, metadata)."""
    return [sc for sc in dep.child_scalars if sc.name not in _DEP_INLINE_TAIL_SCALAR_NAMES]


def _concrete_dep_inline_tail_output_lines(dep: DependentSpec, *, field_indent: str = "                ") -> list[str]:
    """Emit all tail fields in ``_DEP_INLINE_CONVENTION_TAIL_ORDER`` when present on the child model (output only)."""
    scalars_by_name = {sc.name: sc for sc in dep.child_scalars}
    fks_by_name = {fk.name: fk for fk in dep.child_fks}
    out: list[str] = []
    for name in _DEP_INLINE_CONVENTION_TAIL_ORDER:
        if name == "is_deleted":
            if _model_has_field(dep.child_model, "deleted_at"):
                out.append(f'{field_indent}"is_deleted": serializers.BooleanField(),')
            continue
        if name == "deleted_by":
            fk = fks_by_name.get("deleted_by")
            if fk is not None:
                out.append(_inline_fk_output_str(fk, dict_key=True, field_indent=field_indent))
            continue
        sc = scalars_by_name.get(name)
        if sc is not None:
            out.append(_inline_scalar_output_str(sc, model=dep.child_model, dict_key=True, field_indent=field_indent))
    return out


def _concrete_dep_inline_tail_input_create_lines(
    dep: DependentSpec, *, field_indent: str = "                "
) -> list[str]:
    """Emit only client-writable tail fields for nested create input.

    Server-managed fields (``created_at``, ``updated_at``, ``deleted_at``, ``deleted_by``,
    ``is_deleted``) are intentionally excluded — the same rule that applies to the root
    ``InputSerializer`` applies to every nested inline.  Only ``is_visible`` and ``metadata``
    are writable by the client.
    """
    scalars_by_name = {sc.name: sc for sc in dep.child_scalars}
    out: list[str] = []
    for name in _DEP_INLINE_CONVENTION_TAIL_ORDER:
        if name not in _DEP_INPUT_WRITABLE_TAIL:
            continue
        sc = scalars_by_name.get(name)
        if sc is not None:
            expr = _inline_scalar_input_str(sc, model=dep.child_model)
            out.append(f'{field_indent}"{sc.name}": {expr},')
    return out


def _concrete_dep_inline_tail_input_update_lines(
    dep: DependentSpec, *, field_indent: str = "                "
) -> list[str]:
    """Emit only client-writable tail fields for nested update input (same rule as create)."""
    scalars_by_name = {sc.name: sc for sc in dep.child_scalars}
    out: list[str] = []
    for name in _DEP_INLINE_CONVENTION_TAIL_ORDER:
        if name not in _DEP_INPUT_WRITABLE_TAIL:
            continue
        sc = scalars_by_name.get(name)
        if sc is not None:
            expr = _inline_scalar_input_str(sc, model=dep.child_model)
            out.append(f'{field_indent}"{sc.name}": {expr},')
    return out


def _concrete_dep_output_field_lines(dep: DependentSpec, *, field_indent: str) -> list[str]:
    """Recursively build field lines for a concrete dependent's output inline_serializer body.

    Handles arbitrary-depth non-datatype children by recursing with a deeper indent.
    Datatype children (HumanName, Identifier, …) always use the shared *OutputSerializer.
    """
    sub_indent = field_indent + "    "  # for `fields={` of nested inline
    inner_indent = field_indent + "        "  # for field lines inside nested inline
    lines: list[str] = []

    lines.append(f'{field_indent}"id": serializers.UUIDField(),')

    if _is_extension_values_dependent(dep):
        raise ValueError("extension value dependents are rendered separately")

    for m2m in dep.child_m2m:
        if _fk_related_is_terminology_concept(m2m):
            lines.append(f'{field_indent}"{m2m.name}": ConceptCompactSerializer(many=True),')

    for fk in _concrete_dep_inline_other_fks(dep):
        lines.append(_inline_fk_output_str(fk, dict_key=True, field_indent=field_indent))

    for sc in _concrete_dep_inline_other_scalars(dep):
        lines.append(_inline_scalar_output_str(sc, model=dep.child_model, dict_key=True, field_indent=field_indent))

    for sub in dep.children:
        if _is_extension_values_dependent(sub):
            many_kw = "many=True" if sub.is_many else ""
            lines.append(f'{field_indent}"{sub.accessor}": {_EXTENSION_VALUE_OUTPUT_SERIALIZER}({many_kw}),')
        elif sub.is_reference_domain_resource:
            compact = f"{sub.child_model.__name__}CompactSerializer"
            many_kw = "many=True" if sub.is_many else ""
            lines.append(f'{field_indent}"{sub.accessor}": {compact}({many_kw}),')
        elif sub.datatype_base:
            sub_ser = DATATYPE_ABSTRACT_TO_SERIALIZERS[sub.datatype_base][0]
            alias = _dep_datatype_sub_api_key(sub)
            source_arg = f', source="{sub.accessor}"' if alias != sub.accessor else ""
            if sub.is_many:
                lines.append(f'{field_indent}"{alias}": {sub_ser}(many=True{source_arg}),')
            else:
                src = source_arg.lstrip(", ")
                lines.append(f'{field_indent}"{alias}": {sub_ser}({src}),')
        else:
            sub_field_lines = _concrete_dep_output_field_lines(sub, field_indent=inner_indent)
            many_arg = f"\n{sub_indent}many=True," if sub.is_many else ""
            inner = "\n".join(sub_field_lines)
            lines.append(
                f'{field_indent}"{sub.accessor}": inline_serializer(\n'
                f"{sub_indent}fields={{\n"
                f"{inner}\n"
                f"{sub_indent}}},{many_arg}\n"
                f"{field_indent}),"
            )

    lines.extend(_concrete_dep_inline_tail_output_lines(dep, field_indent=field_indent))
    return lines


def _concrete_dep_input_create_field_lines(dep: DependentSpec, *, field_indent: str) -> list[str]:
    """Recursively build field lines for a concrete dependent's CREATE input inline_serializer body.

    Server-managed fields (timestamps, soft-delete, audit) are excluded from every level.
    Datatype children use their shared *CreateSerializer.  Non-datatype children recurse.
    """
    sub_indent = field_indent + "    "
    inner_indent = field_indent + "        "
    lines: list[str] = []

    if _is_extension_values_dependent(dep):
        raise ValueError("extension value dependents are rendered separately")

    for fk in _concrete_dep_inline_other_fks(dep):
        null_arg = "required=False, allow_null=True" if not fk.required else ""
        if _fk_related_is_content_type(fk):
            lines.append(f'{field_indent}"{fk.name}": ContentTypeNaturalKeyField(source="{fk.name}_id", {null_arg}),')
        else:
            lines.append(f'{field_indent}"{fk.name}_id": serializers.UUIDField({null_arg}),')

    for m2m in dep.child_m2m:
        lines.append(
            f'{field_indent}"{m2m.name}": serializers.ListField('
            f"child=serializers.UUIDField(), required=False, allow_empty=True),"
        )

    for sc in _concrete_dep_inline_other_scalars(dep):
        expr = _inline_scalar_input_str(sc, model=dep.child_model)
        lines.append(f'{field_indent}"{sc.name}": {expr},')

    for sub in dep.children:
        if sub.is_reference_domain_resource:
            # Reference resources are managed via their own CRUD endpoints — never inlined,
            # never written through a parent's create payload.
            continue
        if _is_extension_values_dependent(sub):
            if sub.is_many:
                lines.append(
                    f'{field_indent}"{sub.accessor}": {_EXTENSION_VALUE_CREATE_INPUT_SERIALIZER}(many=True, required=False),'
                )
            else:
                lines.append(
                    f'{field_indent}"{sub.accessor}": {_EXTENSION_VALUE_CREATE_INPUT_SERIALIZER}(required=False, allow_null=True),'
                )
        elif sub.datatype_base:
            sub_ser = DATATYPE_ABSTRACT_TO_SERIALIZERS[sub.datatype_base][1]
            api_key = _dep_datatype_sub_api_key(sub)
            if sub.is_many:
                lines.append(f'{field_indent}"{api_key}": {sub_ser}(many=True, required=False),')
            else:
                lines.append(f'{field_indent}"{api_key}": {sub_ser}(required=False, allow_null=True),')
        else:
            sub_field_lines = _concrete_dep_input_create_field_lines(sub, field_indent=inner_indent)
            many_arg = f"\n{sub_indent}many=True," if sub.is_many else ""
            inner = "\n".join(sub_field_lines)
            lines.append(
                f'{field_indent}"{sub.accessor}": inline_serializer(\n'
                f"{sub_indent}required=False,\n"
                f"{sub_indent}fields={{\n"
                f"{inner}\n"
                f"{sub_indent}}},{many_arg}\n"
                f"{field_indent}),"
            )

    lines.extend(_concrete_dep_inline_tail_input_create_lines(dep, field_indent=field_indent))
    return lines


def _concrete_dep_input_update_field_lines(dep: DependentSpec, *, field_indent: str) -> list[str]:
    """Recursively build field lines for a concrete dependent's UPDATE input inline_serializer body.

    Includes an optional ``id`` for identifying existing child rows.
    Server-managed fields are excluded (same rule as create).
    """
    sub_indent = field_indent + "    "
    inner_indent = field_indent + "        "
    lines: list[str] = []

    if _is_extension_values_dependent(dep):
        raise ValueError("extension value dependents are rendered separately")

    lines.append(f'{field_indent}"id": serializers.UUIDField(required=False),')

    for fk in _concrete_dep_inline_other_fks(dep):
        if _fk_related_is_content_type(fk):
            lines.append(
                f'{field_indent}"{fk.name}": ContentTypeNaturalKeyField(source="{fk.name}_id", required=False, allow_null=True),'
            )
        else:
            lines.append(f'{field_indent}"{fk.name}_id": serializers.UUIDField(required=False, allow_null=True),')

    for m2m in dep.child_m2m:
        lines.append(
            f'{field_indent}"{m2m.name}": serializers.ListField('
            "child=serializers.UUIDField(), required=False, allow_empty=True, allow_null=True),"
        )

    for sc in _concrete_dep_inline_other_scalars(dep):
        expr = _inline_scalar_input_str(sc, model=dep.child_model)
        lines.append(f'{field_indent}"{sc.name}": {expr},')

    for sub in dep.children:
        if sub.is_reference_domain_resource:
            continue
        if _is_extension_values_dependent(sub):
            if sub.is_many:
                lines.append(
                    f'{field_indent}"{sub.accessor}": {_EXTENSION_VALUE_UPDATE_INPUT_SERIALIZER}(many=True, required=False),'
                )
            else:
                lines.append(
                    f'{field_indent}"{sub.accessor}": {_EXTENSION_VALUE_UPDATE_INPUT_SERIALIZER}(required=False, allow_null=True),'
                )
        elif sub.datatype_base:
            sub_ser = DATATYPE_ABSTRACT_TO_SERIALIZERS[sub.datatype_base][2]
            api_key = _dep_datatype_sub_api_key(sub)
            if sub.is_many:
                lines.append(f'{field_indent}"{api_key}": {sub_ser}(many=True, required=False),')
            else:
                lines.append(f'{field_indent}"{api_key}": {sub_ser}(required=False, allow_null=True),')
        else:
            sub_field_lines = _concrete_dep_input_update_field_lines(sub, field_indent=inner_indent)
            many_arg = f"\n{sub_indent}many=True," if sub.is_many else ""
            inner = "\n".join(sub_field_lines)
            lines.append(
                f'{field_indent}"{sub.accessor}": inline_serializer(\n'
                f"{sub_indent}required=False,\n"
                f"{sub_indent}fields={{\n"
                f"{inner}\n"
                f"{sub_indent}}},{many_arg}\n"
                f"{field_indent}),"
            )

    lines.extend(_concrete_dep_inline_tail_input_update_lines(dep, field_indent=field_indent))
    return lines


def _render_dep_output_lines(dependents: list[DependentSpec], *, indent: str = "        ") -> list[str]:
    """
    Render output serializer lines for all dependents.

    For datatype-based dependents (HumanName, Address, …) use the existing *OutputSerializer directly.
    For concrete dependents, build an inline_serializer recursively:
      - id
      - M2M fields (e.g. relationship → ConceptCompactSerializer(many=True))
      - non-tail FKs (Concept → ConceptCompactSerializer; …)
      - non-tail scalars (e.g. preferred)
      - sub-children — datatype ones use *OutputSerializer; concrete ones recurse as inline_serializer
      - convention tail: is_visible → is_deleted → deleted_at → deleted_by → created_at → updated_at → metadata
    """
    field_indent = indent + "        "  # 8 extra spaces for field lines inside the inline dict
    lines: list[str] = []
    for dep in dependents:
        if _is_extension_values_dependent(dep):
            if dep.is_many:
                lines.append(f"{indent}{dep.accessor} = {_EXTENSION_VALUE_OUTPUT_SERIALIZER}(many=True)")
            else:
                lines.append(f"{indent}{dep.accessor} = {_EXTENSION_VALUE_OUTPUT_SERIALIZER}()")
            continue
        if dep.is_reference_domain_resource:
            compact = f"{dep.child_model.__name__}CompactSerializer"
            if dep.is_many:
                lines.append(f"{indent}{dep.accessor} = {compact}(many=True)")
            else:
                lines.append(f"{indent}{dep.accessor} = {compact}()")
            continue
        if dep.datatype_base:
            base_out = DATATYPE_ABSTRACT_TO_SERIALIZERS[dep.datatype_base][0]
            ser_name = (
                f"{dep.child_model.__name__}NestedOutputSerializer" if _datatype_dep_extra_scalars(dep) else base_out
            )
            if dep.is_many:
                lines.append(f"{indent}{dep.accessor} = {ser_name}(many=True)")
            else:
                lines.append(f"{indent}{dep.accessor} = {ser_name}()")
        else:
            field_lines = _concrete_dep_output_field_lines(dep, field_indent=field_indent)
            many_arg = f"\n{indent}    many=True," if dep.is_many else ""
            inner = "\n".join(field_lines)
            lines.append(
                f"{indent}{dep.accessor} = inline_serializer(\n"
                f"{indent}    fields={{\n"
                f"{inner}\n"
                f"{indent}    }},{many_arg}\n"
                f"{indent})"
            )
    return lines


def _inline_scalar_input_str(sc: ScalarFieldSpec, *, model: type[models.Model]) -> str:
    """Return a DRF serializer expression for a child scalar in an input (create/update) context."""
    f = sc.django_field
    nullable = getattr(f, "null", False)
    optional_args = "required=False, allow_null=True" if nullable else "required=False"
    if isinstance(f, ArrayField):
        child_expr = _postgres_array_to_listfield_child_expr(model, f.base_field)
        return f"serializers.ListField(child={child_expr}, required=False, allow_empty=True, allow_null=True)"
    if isinstance(f, models.BooleanField):
        return "serializers.BooleanField(required=False)"
    if isinstance(f, models.PositiveSmallIntegerField):
        return f"serializers.IntegerField({optional_args})"
    if isinstance(f, models.IntegerField):
        return f"serializers.IntegerField({optional_args})"
    if isinstance(f, models.UUIDField):
        return f"serializers.UUIDField({optional_args})"
    if isinstance(f, models.DateTimeField):
        return "serializers.DateTimeField(required=False, allow_null=True)"
    if isinstance(f, models.DateField):
        return "serializers.DateField(required=False, allow_null=True)"
    if isinstance(f, models.TimeField):
        return "serializers.TimeField(required=False, allow_null=True)"
    if isinstance(f, models.JSONField):
        return "serializers.JSONField(required=False)"
    if isinstance(f, models.DecimalField):
        extra: list[str] = ["required=False"]
        if nullable:
            extra.append("allow_null=True")
        return _drf_decimal_field_expr(f, extra_parts=tuple(extra))
    if isinstance(f, models.FloatField):
        return "serializers.FloatField(required=False, allow_null=True)"
    if isinstance(f, models.URLField):
        return "serializers.URLField(required=False, allow_blank=True)"
    if isinstance(f, (models.TextField, models.CharField)):
        return "serializers.CharField(required=False, allow_blank=True)"
    return "serializers.CharField(required=False, allow_null=True)"


def _render_dep_create_lines(dependents: list[DependentSpec], *, indent: str = "        ") -> list[str]:
    """Render the create input serializer lines for all dependents."""
    field_indent = indent + "        "
    lines: list[str] = []
    for dep in dependents:
        if dep.is_reference_domain_resource:
            continue
        if dep.datatype_base:
            base_create = DATATYPE_ABSTRACT_TO_SERIALIZERS[dep.datatype_base][1]
            ser_name = (
                f"{dep.child_model.__name__}NestedCreateSerializer" if _datatype_dep_extra_scalars(dep) else base_create
            )
            if dep.is_many:
                lines.append(f"{indent}{dep.accessor} = {ser_name}(many=True, required=False)")
            else:
                lines.append(f"{indent}{dep.accessor} = {ser_name}(required=False, allow_null=True)")
        elif _is_extension_values_dependent(dep):
            if dep.is_many:
                lines.append(
                    f"{indent}{dep.accessor} = {_EXTENSION_VALUE_CREATE_INPUT_SERIALIZER}(many=True, required=False)"
                )
            else:
                lines.append(
                    f"{indent}{dep.accessor} = {_EXTENSION_VALUE_CREATE_INPUT_SERIALIZER}(required=False, allow_null=True)"
                )
        else:
            field_lines = _concrete_dep_input_create_field_lines(dep, field_indent=field_indent)
            many_arg = f"\n{indent}    many=True," if dep.is_many else ""
            inner = "\n".join(field_lines)
            lines.append(
                f"{indent}{dep.accessor} = inline_serializer(\n"
                f"{indent}    required=False,\n"
                f"{indent}    fields={{\n"
                f"{inner}\n"
                f"{indent}    }},{many_arg}\n"
                f"{indent})"
            )
    return lines


def _render_dep_update_lines(dependents: list[DependentSpec], *, indent: str = "        ") -> list[str]:
    """Render the update input serializer lines for all dependents."""
    field_indent = indent + "        "
    lines: list[str] = []
    for dep in dependents:
        if dep.is_reference_domain_resource:
            continue
        if dep.datatype_base:
            base_update = DATATYPE_ABSTRACT_TO_SERIALIZERS[dep.datatype_base][2]
            ser_name = (
                f"{dep.child_model.__name__}NestedUpdateSerializer" if _datatype_dep_extra_scalars(dep) else base_update
            )
            if dep.is_many:
                lines.append(f"{indent}{dep.accessor} = {ser_name}(many=True, required=False)")
            else:
                lines.append(f"{indent}{dep.accessor} = {ser_name}(required=False, allow_null=True)")
        elif _is_extension_values_dependent(dep):
            if dep.is_many:
                lines.append(
                    f"{indent}{dep.accessor} = {_EXTENSION_VALUE_UPDATE_INPUT_SERIALIZER}(many=True, required=False)"
                )
            else:
                lines.append(
                    f"{indent}{dep.accessor} = {_EXTENSION_VALUE_UPDATE_INPUT_SERIALIZER}(required=False, allow_null=True)"
                )
        else:
            field_lines = _concrete_dep_input_update_field_lines(dep, field_indent=field_indent)
            many_arg = f"\n{indent}    many=True," if dep.is_many else ""
            inner = "\n".join(field_lines)
            lines.append(
                f"{indent}{dep.accessor} = inline_serializer(\n"
                f"{indent}    required=False,\n"
                f"{indent}    fields={{\n"
                f"{inner}\n"
                f"{indent}    }},{many_arg}\n"
                f"{indent})"
            )
    return lines


def _split_ordered_fields(
    ctx: ScaffoldContext,
) -> tuple[list[ForeignKeySpec | ScalarFieldSpec], list[ForeignKeySpec | ScalarFieldSpec]]:
    """Split ordered_fields into (concrete_model_fields, abstract_mixin_fields)."""
    abstract_names = _field_names_from_abstract_ancestors(ctx.model)
    concrete: list[ForeignKeySpec | ScalarFieldSpec] = []
    mixin: list[ForeignKeySpec | ScalarFieldSpec] = []
    for item in ctx.ordered_fields:
        if item.name in abstract_names:
            mixin.append(item)
        else:
            concrete.append(item)
    return concrete, mixin


def _output_field_items(
    items: list[ForeignKeySpec | ScalarFieldSpec],
    ctx: ScaffoldContext,
) -> list[str]:
    lines = []
    for item in items:
        if isinstance(item, ForeignKeySpec):
            lines.append(_drf_output_line_fk(item))
        else:
            lines.append(_drf_output_line_scalar(ctx, item))
    return lines


def _soft_delete_output_lines() -> list[str]:
    return [
        "        is_deleted = serializers.BooleanField()",
        "        deleted_at = serializers.DateTimeField(required=False, allow_null=True)",
        "        deleted_by = UserCompactSerializer()",
    ]


def _m2m_output_lines(m2m_fields: list[ForeignKeySpec]) -> list[str]:
    lines = []
    for fk in m2m_fields:
        if _fk_related_is_terminology_concept(fk):
            lines.append(f"        {fk.name} = ConceptCompactSerializer(many=True)")
        else:
            rel = fk.related_model.__name__
            lines.append(f"        {fk.name} = {rel}CompactSerializer(many=True)")
    return lines


def _m2m_input_create_lines(m2m_fields: list[ForeignKeySpec]) -> list[str]:
    lines = []
    for fk in m2m_fields:
        lines.append(
            f"        {fk.name} = serializers.ListField(child=serializers.UUIDField(), required=False, allow_empty=True)"
        )
    return lines


def _m2m_input_update_lines(m2m_fields: list[ForeignKeySpec]) -> list[str]:
    lines = []
    for fk in m2m_fields:
        lines.append(
            f"        {fk.name} = serializers.ListField(child=serializers.UUIDField(), required=False, allow_empty=True, allow_null=True)"
        )
    return lines


def _standard_output_body(
    ctx: ScaffoldContext,
    *,
    include_reference_id: bool = True,
    include_revision: bool = False,
    inline_revision: bool = False,
) -> list[str]:
    """
    Canonical output body ordering (mirrors the manually-drafted patient.py):
      id → [reference_id] → concrete model fields
      → dependents (names, identifiers, addresses, contacts …)
      → mixin fields (metadata, is_visible)
      → soft-delete (is_deleted, deleted_at, deleted_by) [always when has_soft_delete]
      → created_at, updated_at
      → [revision]
    """
    concrete, mixin = _split_ordered_fields(ctx)

    lines = ["        id = serializers.UUIDField()"]
    if include_reference_id and ctx.reference_id_field is not None:
        lines.append(_drf_output_line_scalar(ctx, ctx.reference_id_field))

    lines.extend(_output_field_items(concrete, ctx))
    lines.extend(_m2m_output_lines(ctx.m2m_fields))
    lines.extend(_render_dep_output_lines(ctx.dependents))
    lines.extend(_output_field_items(mixin, ctx))

    if ctx.has_soft_delete:
        lines.extend(_soft_delete_output_lines())

    lines.append("        created_at = serializers.DateTimeField()")
    lines.append("        updated_at = serializers.DateTimeField()")

    if inline_revision:
        lines.append("        revision = inline_serializer(")
        lines.append('            source="*",')
        lines.append("            fields={")
        lines.append('                "id": serializers.IntegerField(source="history_id"),')
        lines.append('                "type": serializers.CharField(source="history_type"),')
        lines.append('                "recorded_at": serializers.DateTimeField(source="history_date"),')
        lines.append('                "change_reason": serializers.CharField(source="history_change_reason"),')
        lines.append('                "user": UserCompactSerializer(source="history_user"),')
        lines.append("            },")
        lines.append("        )")
    elif include_revision:
        lines.append("        revision = RevisionSerializer()")

    return lines


def _output_body_lines(ctx: ScaffoldContext) -> list[str]:
    """Create / update / restore response body."""
    return _standard_output_body(ctx)


def _update_output_body_lines(ctx: ScaffoldContext) -> list[str]:
    """Update response body — no reference_id (matches manual patient.py)."""
    return _standard_output_body(ctx, include_reference_id=False)


def _list_output_body_lines(ctx: ScaffoldContext) -> list[str]:
    """List response body."""
    return _standard_output_body(ctx)


def _detail_output_body_lines(ctx: ScaffoldContext) -> list[str]:
    """Detail response body — no revision on the plain detail endpoint."""
    return _standard_output_body(ctx)


def _revert_output_body_lines(ctx: ScaffoldContext) -> list[str]:
    """History-revert response body — includes RevisionSerializer()."""
    return _standard_output_body(ctx, include_revision=True)


def _history_row_output_lines(ctx: ScaffoldContext) -> list[str]:
    """Historical row output (history detail / previous / next) — includes inline revision block."""
    return _standard_output_body(ctx, inline_revision=True)


def _input_create_lines(ctx: ScaffoldContext) -> list[str]:
    lines: list[str] = []
    for item in ctx.ordered_fields:
        if isinstance(item, ForeignKeySpec):
            lines.append(_drf_input_line_fk_create(item))
        else:
            line = _drf_input_line_scalar_create(ctx, item)
            if line:
                lines.append(line)
    lines.extend(_m2m_input_create_lines(ctx.m2m_fields))
    lines.extend(_render_dep_create_lines(ctx.dependents))
    return lines


def _drf_input_line_scalar_update(ctx: ScaffoldContext, spec: ScalarFieldSpec) -> str | None:
    f = spec.django_field
    name = spec.name
    if getattr(f, "auto_now", False) or getattr(f, "auto_now_add", False):
        return None
    if isinstance(f, ArrayField):
        child = _postgres_array_to_listfield_child_expr(ctx.model, f.base_field)
        return (
            f"        {name} = serializers.ListField(child={child}, required=False, allow_empty=True, allow_null=True)"
        )
    arg = _choice_field_choices_argument(ctx.model, f)
    if arg is not None:
        return f"        {name} = serializers.ChoiceField(choices={arg}, required=False, allow_null=True)"
    if isinstance(f, models.BooleanField):
        return f"        {name} = serializers.BooleanField(required=False)"
    if isinstance(f, models.IntegerField):
        return f"        {name} = serializers.IntegerField(required=False, allow_null=True)"
    if isinstance(f, models.UUIDField):
        return f"        {name} = serializers.UUIDField(required=False, allow_null=True)"
    if isinstance(f, models.DateTimeField):
        return f"        {name} = serializers.DateTimeField(required=False, allow_null=True)"
    if isinstance(f, models.DateField):
        return f"        {name} = serializers.DateField(required=False, allow_null=True)"
    if isinstance(f, models.TimeField):
        return f"        {name} = serializers.TimeField(required=False, allow_null=True)"
    if isinstance(f, models.DecimalField):
        return f"        {name} = {_drf_decimal_field_expr(f, extra_parts=('required=False', 'allow_null=True'))}"
    if isinstance(f, models.FloatField):
        return f"        {name} = serializers.FloatField(required=False, allow_null=True)"
    if isinstance(f, models.JSONField):
        return f"        {name} = serializers.JSONField(required=False)"
    if isinstance(f, models.URLField):
        return f"        {name} = serializers.URLField(required=False, allow_blank=True)"
    if isinstance(f, models.EmailField):
        return f"        {name} = serializers.EmailField(required=False, allow_blank=True)"
    if isinstance(f, (models.TextField, models.CharField)):
        return f"        {name} = serializers.CharField(required=False, allow_blank=True)"
    return f"        # TODO: PATCH input for {name} ({type(f).__name__})"


def _input_update_lines(ctx: ScaffoldContext) -> list[str]:
    lines: list[str] = []
    for item in ctx.ordered_fields:
        if isinstance(item, ForeignKeySpec):
            lines.append(_drf_input_line_fk_update(item))
        else:
            line = _drf_input_line_scalar_update(ctx, item)
            if line:
                lines.append(line)
    lines.extend(_m2m_input_update_lines(ctx.m2m_fields))
    lines.extend(_render_dep_update_lines(ctx.dependents))
    return lines


def _history_output_lines(ctx: ScaffoldContext) -> list[str]:
    lines = _output_body_lines(ctx)
    h_choices = '[("+", "Created"), ("~", "Changed"), ("-", "Deleted")]'
    extra = [
        "        history_id = serializers.IntegerField()",
        "        history_date = serializers.DateTimeField()",
        f"        history_type = serializers.ChoiceField(choices={h_choices})",
        "        history_change_reason = serializers.CharField(required=False, allow_null=True)",
        "        history_user_id = serializers.UUIDField(required=False, allow_null=True)",
    ]
    return lines + extra


def _history_list_output_lines_rich() -> list[str]:
    return [
        '        id = serializers.IntegerField(source="history_id")',
        '        recorded_at = serializers.DateTimeField(source="history_date")',
        '        type = serializers.CharField(source="history_type")',
        '        change_reason = serializers.CharField(source="history_change_reason")',
        '        user = UserCompactSerializer(source="history_user")',
    ]


def _order_by_filter_field_lines() -> list[str]:
    return [
        "        order_by = serializers.ChoiceField(",
        "            required=False,",
        "            choices=[",
        '                "created_at",',
        '                "-created_at",',
        '                "updated_at",',
        '                "-updated_at",',
        '                "deleted_at",',
        '                "-deleted_at",',
        "            ],",
        "            help_text=\"Sort by field. Prefix with '-' for descending.\",",
        "        )",
    ]


def _order_by_filter_pairs() -> list[str]:
    return [
        '            ("created_at", "created_at"),',
        '            ("updated_at", "updated_at"),',
        '            ("deleted_at", "deleted_at"),',
    ]


def _has_optional_query_boolean_filter(ctx: ScaffoldContext) -> bool:
    for item in ctx.ordered_fields:
        if isinstance(item, ScalarFieldSpec) and isinstance(item.django_field, models.BooleanField):
            return True
    return False


def resource_list_query_body_lines(ctx: ScaffoldContext) -> list[str]:
    """Body lines for ``{Model}ListQuerySerializer`` (shared with serializers module).

    Ordering is provided by ``ListOrderingMixin`` on that serializer, not duplicated here.
    """
    lines: list[str] = []
    if ctx.has_visible:
        lines.append("        is_visible = serializers.BooleanField(required=False, default=True)")
    if ctx.has_soft_delete:
        lines.append("        is_deleted = serializers.BooleanField(required=False, default=False)")
    if ctx.reference_id_field is not None:
        lines.append("        reference_id = serializers.CharField(required=False)")
    for item in ctx.ordered_fields:
        if isinstance(item, ForeignKeySpec):
            if _fk_related_is_content_type(item):
                lines.append(
                    f'        {item.name} = ContentTypeNaturalKeyField(source="{item.name}_id", required=False)'
                )
            else:
                lines.append(f"        {item.name}_id = serializers.UUIDField(required=False)")
                if _fk_related_is_terminology_concept(item):
                    lines.append(f"        {item.name}_code = serializers.CharField(required=False)")
        elif isinstance(item.django_field, models.BooleanField):
            lines.append(f"        {item.name} = OptionalQueryBooleanField()")
        elif isinstance(item.django_field, (models.CharField, models.TextField)):
            lines.append(f"        {item.name} = serializers.CharField(required=False)")
    lines.extend([
        "        limit = serializers.IntegerField(required=False, min_value=1, max_value=100, default=10)",
        "        offset = serializers.IntegerField(required=False, min_value=0, default=0)",
    ])
    return lines


def resource_serializers_import_block(ctx: ScaffoldContext) -> str:
    """Import compact from ``compacts`` and other serializers from the resource module."""

    m = ctx.model_name
    compact_line = f"from {ctx.app_python_path}.serializers.compacts import {m}CompactSerializer\n"
    names = [
        f"{m}BulkUpdateItemInputSerializer",
        f"{m}CreateInputSerializer",
        f"{m}DetailOutputSerializer",
        f"{m}ListOutputSerializer",
        f"{m}ListQuerySerializer",
        f"{m}UpdateInputSerializer",
    ]
    if ctx.has_history:
        names.append(f"{m}HistoryDetailOutputSerializer")
    if ctx.with_history_extras:
        names.extend([
            f"{m}HistoryDiffQuerySerializer",
            f"{m}HistoryNextOutputSerializer",
            f"{m}HistoryPreviousOutputSerializer",
            f"{m}HistoryRevertOutputSerializer",
        ])
    joined = ",\n".join(f"    {n}" for n in sorted(names))
    rest = f"from {ctx.app_python_path}.serializers.{ctx.resource_module} import (\n{joined},\n)\n\n\n"
    return compact_line + "\n" + rest


def compact_serializer_export_names(ctx: ScaffoldContext) -> list[str]:
    return [f"{ctx.model_name}CompactSerializer"]


def serializer_export_names(ctx: ScaffoldContext) -> list[str]:
    """Serializer class names exported from ``serializers/__init__.py`` (non-compact)."""
    m = ctx.model_name
    names = [
        f"{m}BulkUpdateItemInputSerializer",
        f"{m}CreateInputSerializer",
        f"{m}UpdateInputSerializer",
        f"{m}ListQuerySerializer",
        f"{m}ListOutputSerializer",
        f"{m}DetailOutputSerializer",
    ]
    if ctx.has_history:
        names.append(f"{m}HistoryDetailOutputSerializer")
    if ctx.with_history_extras:
        names.extend([
            f"{m}HistoryPreviousOutputSerializer",
            f"{m}HistoryNextOutputSerializer",
            f"{m}HistoryRevertOutputSerializer",
            f"{m}HistoryDiffQuerySerializer",
        ])
    return names


def _entity_snake(model_name: str) -> str:
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", model_name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _plural_snake(resource_module: str) -> str:
    """Derive plural form for get_<plural> selector (e.g. policy → policies)."""
    if resource_module.endswith("y") and not resource_module.endswith(("ay", "ey", "oy", "uy")):
        return resource_module[:-1] + "ies"
    if resource_module.endswith("s"):
        return resource_module + "es"
    return resource_module + "s"


def _get_plural_label(ctx: ScaffoldContext) -> str:
    return str(ctx.model._meta.verbose_name_plural or f"{ctx.model_name}s").lower()


def _get_verbose_name_lower(ctx: ScaffoldContext) -> str:
    return str(ctx.model._meta.verbose_name or ctx.model_name).lower()


def _apis_selector_import_block(ctx: ScaffoldContext, *, es: str, selector_plural: str) -> str:
    lines: list[str] = [
        f"get_{es},",
    ]
    if ctx.has_history:
        lines.extend([
            f"    get_{es}_history,",
            f"    get_{es}_history_record,",
        ])
    lines.append(f"    get_{selector_plural},")
    if ctx.with_history_extras:
        lines.extend([
            f"    get_{es}_history_diff,",
            f"    get_{es}_history_next_record,",
            f"    get_{es}_history_previous_record,",
        ])
    if ctx.with_crud_audit:
        lines.extend([
            f"    get_{es}_model_crud_events,",
            f"    get_{es}_object_crud_events,",
        ])
    return "\n".join(lines) + "\n"


def _apis_service_import_block(ctx: ScaffoldContext, *, es: str) -> str:
    lines: list[str] = [f"{es}_create,"]
    if ctx.has_soft_delete:
        lines.extend([
            f"    {es}_delete,",
            f"    {es}_hard_delete,",
            f"    {es}_restore,",
        ])
    lines.append(f"    {es}_update,")
    if ctx.with_history_extras:
        lines.insert(-1, f"    {es}_revert_to_history,")
    return "\n".join(lines) + "\n"


def _apis_extra_top_imports(ctx: ScaffoldContext) -> str:
    """Imports for thin API modules (serializers live under ``serializers.<resource>``)."""
    parts: list[str] = []
    if ctx.with_history_extras:
        parts.append("from django.http import Http404")

    parts.append("from core.api.views import AuthorizedAPIView")
    parts.append("from core.common.services import bulk_run_via_service")

    api_ser_names: list[str] = [
        "build_bulk_input_serializer",
        "build_bulk_output_serializer",
        "build_paginated_result_serializer",
        "build_success_response_serializer",
    ]
    if ctx.has_soft_delete:
        api_ser_names.append("build_bulk_ids_input_serializer")
    if ctx.has_history:
        api_ser_names.extend(["HistoryListItemSerializer", "RevisionSerializer"])
    if ctx.with_history_extras:
        api_ser_names.append("HistoryDiffResponseSerializer")
    if ctx.with_crud_audit:
        api_ser_names.extend(["CrudEventAuditListFilterSerializer", "CrudEventOutputSerializer"])
    parts.append(f"from core.api.serializers import {', '.join(sorted(api_ser_names))}")

    return "\n".join(parts) + "\n\n"


def _render_apis_bulk(
    ctx: ScaffoldContext,
    *,
    es: str,
    tag_const: str,
    verbose: str,
    list_label: str,
    auth_prefix: str,
    auth_resource: str,
) -> str:
    """Render ``BulkCreateApi`` / ``BulkUpdateApi`` / ``BulkDeleteApi`` for a resource.

    ``BulkDeleteApi`` is only emitted when the resource supports soft-delete (its
    service layer provides ``<es>_delete``).
    """

    m = ctx.model_name
    bulk_delete_block = ""
    if ctx.has_soft_delete:
        bulk_delete_block = f"""


class {m}BulkDeleteApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:delete"

    InputSerializer = build_bulk_ids_input_serializer(
        component_name="{m}BulkDeleteInput",
    )

    @extend_schema(
        operation_id="{ctx.app_label}_{es}_bulk_delete",
        tags=[{tag_const}],
        request=InputSerializer,
        responses={{204: None}},
        description=(
            "Soft-delete multiple {list_label} in a single atomic transaction. "
            "Per-item validation errors are aggregated and returned together; "
            "any failure rolls back the entire batch."
        ),
        summary="Bulk delete {list_label}",
    )
    def post(self, request) -> Response:
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items = [{{"id": id_}} for id_ in serializer.validated_data["ids"]]
        bulk_run_via_service(
            items=items,
            run_one={es}_delete,
            shared_kwargs={{"requesting_user": request.user}},
        )

        return Response(status=status.HTTP_204_NO_CONTENT)"""

    return f"""


class {m}BulkCreateApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:create"

    InputSerializer = build_bulk_input_serializer(
        component_name="{m}BulkCreateInput",
        item_serializer={m}CreateInputSerializer,
    )
    OutputSerializer = build_bulk_output_serializer(
        component_name="{m}BulkCreateOutput",
        item_serializer={m}CompactSerializer,
    )
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="{m}BulkCreateSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="{ctx.app_label}_{es}_bulk_create",
        tags=[{tag_const}],
        request=InputSerializer,
        responses={{201: SuccessResponseSerializer}},
        description=(
            "Create multiple {list_label} in a single atomic transaction. "
            "Per-item validation errors are aggregated and returned together; "
            "any failure rolls back the entire batch."
        ),
        summary="Bulk create {list_label}",
    )
    def post(self, request) -> Response:
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        created = bulk_run_via_service(
            items=serializer.validated_data["items"],
            run_one={es}_create,
            shared_kwargs={{"requesting_user": request.user}},
        )

        return_data = self.OutputSerializer({{"items": created}}).data
        return Response(data=return_data, status=status.HTTP_201_CREATED)


class {m}BulkUpdateApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:update"

    InputSerializer = build_bulk_input_serializer(
        component_name="{m}BulkUpdateInput",
        item_serializer={m}BulkUpdateItemInputSerializer,
    )
    OutputSerializer = build_bulk_output_serializer(
        component_name="{m}BulkUpdateOutput",
        item_serializer={m}CompactSerializer,
    )
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="{m}BulkUpdateSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="{ctx.app_label}_{es}_bulk_update",
        tags=[{tag_const}],
        request=InputSerializer,
        responses={{200: SuccessResponseSerializer}},
        description=(
            "Update multiple {list_label} in a single atomic transaction. "
            "Each item must include its ``id`` plus the partial fields to "
            "change. Per-item validation errors are aggregated and returned "
            "together; any failure rolls back the entire batch."
        ),
        summary="Bulk update {list_label}",
    )
    def patch(self, request) -> Response:
        serializer = self.InputSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        prepared = [
            {{"id": item.pop("id"), "data": item}}
            for item in serializer.validated_data["items"]
        ]
        updated = bulk_run_via_service(
            items=prepared,
            run_one={es}_update,
            shared_kwargs={{"requesting_user": request.user}},
        )

        return_data = self.OutputSerializer({{"items": updated}}).data
        return Response(data=return_data, status=status.HTTP_200_OK){bulk_delete_block}
"""


def _render_apis_history_extras(
    ctx: ScaffoldContext, *, es: str, tag_const: str, verbose: str, auth_prefix: str, auth_resource: str, cache_ns: str
) -> str:
    """History previous/next, diff, revert — requires ``with_history_extras``."""
    return f"""


class {ctx.model_name}HistoryPreviousApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:history:retrieve"

    OutputSerializer = {ctx.model_name}HistoryPreviousOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="{ctx.model_name}HistoryPreviousSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="{ctx.app_label}_{es}_history_previous",
        tags=[{tag_const}],
        responses={{200: SuccessResponseSerializer, 404: None}},
        description="Get the older adjacent historical row relative to ``history_id``, if any.",
        summary="Get previous {verbose} history record",
    )
    @cache_api_response(namespace="{cache_ns}", resource_id_kwarg="id")
    def get(self, request, id: UUID, history_id: int) -> Response:
        get_{es}(id=id, requesting_user=request.user)
        record = get_{es}_history_previous_record(
            id=id,
            history_id=history_id,
            requesting_user=request.user,
        )
        if record is None:
            raise Http404
        return Response(data=self.OutputSerializer(record).data, status=status.HTTP_200_OK)


class {ctx.model_name}HistoryNextApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:history:retrieve"

    OutputSerializer = {ctx.model_name}HistoryNextOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="{ctx.model_name}HistoryNextSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="{ctx.app_label}_{es}_history_next",
        tags=[{tag_const}],
        responses={{200: SuccessResponseSerializer, 404: None}},
        description="Get the newer adjacent historical row relative to ``history_id``, if any.",
        summary="Get next {verbose} history record",
    )
    @cache_api_response(namespace="{cache_ns}", resource_id_kwarg="id")
    def get(self, request, id: UUID, history_id: int) -> Response:
        get_{es}(id=id, requesting_user=request.user)
        record = get_{es}_history_next_record(
            id=id,
            history_id=history_id,
            requesting_user=request.user,
        )
        if record is None:
            raise Http404
        return Response(data=self.OutputSerializer(record).data, status=status.HTTP_200_OK)


class {ctx.model_name}HistoryDiffApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:history:diff"

    QuerySerializer = {ctx.model_name}HistoryDiffQuerySerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="{ctx.model_name}HistoryDiffSuccessResponse",
        result_serializer=HistoryDiffResponseSerializer,
    )

    @extend_schema(
        operation_id="{ctx.app_label}_{es}_history_diff",
        tags=[{tag_const}],
        parameters=[QuerySerializer],
        responses={{200: SuccessResponseSerializer}},
        description="Diff two historical versions of the same {verbose}.",
        summary="Diff two {verbose} history records",
    )
    @cache_api_response(namespace="{cache_ns}", resource_id_kwarg="id")
    def get(self, request, id: UUID) -> Response:
        get_{es}(id=id, requesting_user=request.user)

        qs = self.QuerySerializer(data=request.query_params)
        qs.is_valid(raise_exception=True)
        validated = cast(dict[str, Any], qs.validated_data)

        delta = get_{es}_history_diff(
            id=id,
            from_history_id=validated["from_history_id"],
            to_history_id=validated["to_history_id"],
            requesting_user=request.user,
        )
        return_data = model_delta_to_api_dict(delta=delta)
        return Response(data=return_data, status=status.HTTP_200_OK)


class {ctx.model_name}HistoryRevertApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:history:revert"

    OutputSerializer = {ctx.model_name}HistoryRevertOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="{ctx.model_name}HistoryRevertSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="{ctx.app_label}_{es}_history_revert",
        tags=[{tag_const}],
        request=None,
        responses={{200: SuccessResponseSerializer}},
        description="Revert the live {verbose} to the snapshot at ``history_id`` (creates a new history row).",
        summary="Revert {verbose} to a history snapshot",
    )
    def post(self, request, id: UUID, history_id: int) -> Response:
        run_service({es}_revert_to_history, {{}}, id=id, history_id=history_id, requesting_user=request.user)
        detail = get_{es}(id=id, requesting_user=request.user)
        return Response(data=self.OutputSerializer(detail).data, status=status.HTTP_200_OK)
"""


def _render_apis_crud_audit(
    ctx: ScaffoldContext, *, es: str, tag_const: str, verbose: str, auth_prefix: str, auth_resource: str, cache_ns: str
) -> str:
    return f"""


class {ctx.model_name}ObjectCrudAuditListApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:audit:object:list"

    class Pagination(LimitOffsetPagination):
        default_limit = 20
        max_limit = 100

    PaginatedResultSerializer = build_paginated_result_serializer(
        component_name="{ctx.model_name}ObjectCrudAuditPaginatedResult",
        item_serializer=CrudEventOutputSerializer,
    )
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="{ctx.model_name}ObjectCrudAuditSuccessResponse",
        result_serializer=PaginatedResultSerializer,
    )

    @extend_schema(
        operation_id="{ctx.app_label}_{ctx.model_name.lower()}_audit_object_list",
        tags=[{tag_const}],
        parameters=[CrudEventAuditListFilterSerializer],
        responses={{200: SuccessResponseSerializer}},
        description="List CRUD audit events for one {verbose}.",
        summary="List CRUD events for one {verbose}",
    )
    @cache_api_response(namespace="{cache_ns}", resource_id_kwarg="id")
    def get(self, request, id: UUID) -> Response:
        filters_serializer = CrudEventAuditListFilterSerializer(data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = cast(dict[str, Any], filters_serializer.validated_data)
        queryset = get_{es}_object_crud_events(
            id=id,
            filters=filters,
            requesting_user=request.user,
        )
        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=CrudEventOutputSerializer,
            queryset=queryset,
            request=request,
            view=self,
        )


class {ctx.model_name}ModelCrudAuditListApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:audit:model:list"

    class Pagination(LimitOffsetPagination):
        default_limit = 20
        max_limit = 100

    PaginatedResultSerializer = build_paginated_result_serializer(
        component_name="{ctx.model_name}ModelCrudAuditPaginatedResult",
        item_serializer=CrudEventOutputSerializer,
    )
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="{ctx.model_name}ModelCrudAuditSuccessResponse",
        result_serializer=PaginatedResultSerializer,
    )

    @extend_schema(
        operation_id="{ctx.app_label}_{ctx.model_name.lower()}_audit_model_list",
        tags=[{tag_const}],
        parameters=[CrudEventAuditListFilterSerializer],
        responses={{200: SuccessResponseSerializer}},
        description="List CRUD audit events for all {verbose} rows (model scope).",
        summary="List CRUD events for all {verbose} (model scope)",
    )
    @cache_api_response(namespace="{cache_ns}")
    def get(self, request) -> Response:
        filters_serializer = CrudEventAuditListFilterSerializer(data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)
        filters = cast(dict[str, Any], filters_serializer.validated_data)
        queryset = get_{es}_model_crud_events(
            filters=filters,
            requesting_user=request.user,
        )
        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=CrudEventOutputSerializer,
            queryset=queryset,
            request=request,
            view=self,
        )
"""


def render_apis_py(ctx: ScaffoldContext) -> str:
    es = _entity_snake(ctx.model_name)
    selector_plural = _plural_snake(ctx.resource_module)
    import_selectors = _apis_selector_import_block(ctx, es=es, selector_plural=selector_plural)
    import_services = _apis_service_import_block(ctx, es=es)
    extra_top = _apis_extra_top_imports(ctx)
    ser_block = resource_serializers_import_block(ctx)

    list_label = _get_plural_label(ctx)
    verbose = _get_verbose_name_lower(ctx)
    tag_const = ctx.openapi_tag_constant_name
    auth_resource = ctx.model_name
    auth_prefix = f"{ctx.app_label}:{ctx.model_name.lower()}"

    cache_ns = f"{es}:list"

    detail_get_line = f"        obj = get_{es}(id=id, requesting_user=request.user)"

    utils_import = (
        "from core.api.utils import cache_api_response, model_delta_to_api_dict, run_service"
        if ctx.with_history_extras
        else "from core.api.utils import cache_api_response, run_service"
    )

    spectacular_import = "from drf_spectacular.utils import extend_schema"
    rest_rf_import = "from rest_framework import status"

    history_api_block = ""
    if ctx.has_history:
        history_api_block = f"""

class {ctx.model_name}HistoryListApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:history:list"

    class Pagination(LimitOffsetPagination):
        default_limit = 10
        max_limit = 100

    OutputSerializer = HistoryListItemSerializer

    PaginatedResultSerializer = build_paginated_result_serializer(
        component_name="{ctx.model_name}HistoryListPaginatedResult",
        item_serializer=OutputSerializer,
    )
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="{ctx.model_name}HistoryListSuccessResponse",
        result_serializer=PaginatedResultSerializer,
    )

    @extend_schema(
        operation_id="{ctx.app_label}_{es}_history_list",
        tags=[{tag_const}],
        responses={{200: SuccessResponseSerializer}},
        description="List version history for this {verbose}, newest first.",
        summary="List {verbose} history",
    )
    @cache_api_response(namespace="{cache_ns}", resource_id_kwarg="id")
    def get(self, request, id: UUID) -> Response:
        get_{es}(id=id, requesting_user=request.user)
        queryset = get_{es}_history(id=id, requesting_user=request.user)
        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.OutputSerializer,
            queryset=queryset,
            request=request,
            view=self,
        )


class {ctx.model_name}HistoryDetailApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:history:retrieve"

    OutputSerializer = {ctx.model_name}HistoryDetailOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="{ctx.model_name}HistoryDetailSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="{ctx.app_label}_{es}_history_detail",
        tags=[{tag_const}],
        responses={{200: SuccessResponseSerializer}},
        description="Get a single historical version of this {verbose}.",
        summary="Get {verbose} history record",
    )
    @cache_api_response(namespace="{cache_ns}", resource_id_kwarg="id")
    def get(self, request, id: UUID, history_id: int) -> Response:
        get_{es}(id=id, requesting_user=request.user)
        record = get_{es}_history_record(id=id, history_id=history_id, requesting_user=request.user)
        return Response(data=self.OutputSerializer(record).data, status=status.HTTP_200_OK)
"""

    bulk_api_block = _render_apis_bulk(
        ctx,
        es=es,
        tag_const=tag_const,
        verbose=verbose,
        list_label=list_label,
        auth_prefix=auth_prefix,
        auth_resource=auth_resource,
    )

    soft_delete_api_block = ""
    if ctx.has_soft_delete:
        soft_delete_api_block = f"""


class {ctx.model_name}DeleteApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:delete"

    @extend_schema(
        tags=[{tag_const}],
        responses={{204: None}},
        description="Soft-delete a {verbose} by ID.",
        summary="Delete {verbose} by ID",
    )
    def delete(self, request, id: UUID) -> Response:
        run_service({es}_delete, {{}}, id=id, requesting_user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class {ctx.model_name}RestoreApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:restore"

    OutputSerializer = {ctx.model_name}CompactSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="{ctx.model_name}RestoreSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        tags=[{tag_const}],
        request=None,
        responses={{200: SuccessResponseSerializer}},
        description="Restore a soft-deleted {verbose} by ID.",
        summary="Restore {verbose} by ID",
    )
    def post(self, request, id: UUID) -> Response:
        obj = run_service({es}_restore, {{}}, id=id, requesting_user=request.user)
        return_data = self.OutputSerializer(obj).data
        return Response(data=return_data, status=status.HTTP_200_OK)


class {ctx.model_name}HardDeleteApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:hard_delete"

    @extend_schema(
        tags=[{tag_const}],
        responses={{204: None}},
        description="Permanently delete a {verbose} by ID.",
        summary="Hard delete {verbose} by ID",
    )
    def delete(self, request, id: UUID) -> Response:
        run_service({es}_hard_delete, {{}}, id=id, requesting_user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
"""

    body = f"""\
from typing import Any, cast
from uuid import UUID

{extra_top}{spectacular_import}
{rest_rf_import}
from rest_framework.response import Response

from core.api.pagination import LimitOffsetPagination, get_paginated_response
{utils_import}
from {ctx.app_python_path}.constants import {tag_const}
from {ctx.app_python_path}.selectors import (
    {import_selectors})
from {ctx.app_python_path}.services import (
    {import_services})
{ser_block}

class {ctx.model_name}CreateApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:create"

    InputSerializer = {ctx.model_name}CreateInputSerializer
    OutputSerializer = {ctx.model_name}CompactSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="{ctx.model_name}CreateSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        tags=[{tag_const}],
        request=InputSerializer,
        responses={{201: SuccessResponseSerializer}},
        description="Create a new {verbose}.",
        summary="Create {verbose}",
    )
    def post(self, request) -> Response:
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = run_service({es}_create, serializer.validated_data, requesting_user=request.user)
        return_data = self.OutputSerializer(result).data

        return Response(data=return_data, status=status.HTTP_201_CREATED)


class {ctx.model_name}ListApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:list"

    class Pagination(LimitOffsetPagination):
        default_limit = 10
        max_limit = 100

    QuerySerializer = {ctx.model_name}ListQuerySerializer
    OutputSerializer = {ctx.model_name}ListOutputSerializer

    PaginatedResultSerializer = build_paginated_result_serializer(
        component_name="{ctx.model_name}ListPaginatedResult",
        item_serializer=OutputSerializer,
    )
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="{ctx.model_name}ListSuccessResponse",
        result_serializer=PaginatedResultSerializer,
    )

    @extend_schema(
        tags=[{tag_const}],
        parameters=[QuerySerializer],
        responses={{200: SuccessResponseSerializer}},
        description="List {list_label} with filters, ordering (order_by), and limit/offset pagination.",
        summary="List {list_label}",
    )
    @cache_api_response(namespace="{cache_ns}")
    def get(self, request) -> Response:
        query_serializer = self.QuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        queryset = get_{selector_plural}(
            filters=cast(dict[str, Any], query_serializer.validated_data),
            requesting_user=request.user,
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.OutputSerializer,
            queryset=queryset,
            request=request,
            view=self,
        )


class {ctx.model_name}DetailApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:retrieve"

    OutputSerializer = {ctx.model_name}DetailOutputSerializer

    SuccessResponseSerializer = build_success_response_serializer(
        component_name="{ctx.model_name}DetailSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        tags=[{tag_const}],
        responses={{200: SuccessResponseSerializer}},
        description="Get one {verbose} by ID.",
        summary="Get {verbose} by ID",
    )
    @cache_api_response(namespace="{cache_ns}", resource_id_kwarg="id")
    def get(self, request, id: UUID) -> Response:
{detail_get_line}
        return_data = self.OutputSerializer(obj).data
        return Response(data=return_data, status=status.HTTP_200_OK)
{history_api_block}

class {ctx.model_name}UpdateApi(AuthorizedAPIView):
    authorization_resource_code = "{auth_resource}"
    authorization_action = "{auth_prefix}:update"

    InputSerializer = {ctx.model_name}UpdateInputSerializer
    OutputSerializer = {ctx.model_name}CompactSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="{ctx.model_name}UpdateSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        tags=[{tag_const}],
        request=InputSerializer,
        responses={{200: SuccessResponseSerializer}},
        description="Update a {verbose} by ID.",
        summary="Update {verbose} by ID",
    )
    def patch(self, request, id: UUID) -> Response:
        serializer = self.InputSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        obj = run_service(
            {es}_update,
            serializer.validated_data,
            id=id,
            _as="data",
            requesting_user=request.user,
        )
        return_data = self.OutputSerializer(obj).data
        return Response(data=return_data, status=status.HTTP_200_OK)
{soft_delete_api_block}{bulk_api_block}
"""
    suffix = ""
    if ctx.with_history_extras:
        suffix += _render_apis_history_extras(
            ctx,
            es=es,
            tag_const=tag_const,
            verbose=verbose,
            auth_prefix=auth_prefix,
            auth_resource=auth_resource,
            cache_ns=cache_ns,
        )
    if ctx.with_crud_audit:
        suffix += _render_apis_crud_audit(
            ctx,
            es=es,
            tag_const=tag_const,
            verbose=verbose,
            auth_prefix=auth_prefix,
            auth_resource=auth_resource,
            cache_ns=cache_ns,
        )
    return textwrap.dedent(body + suffix)


def _revert_model_update_field_names(ctx: ScaffoldContext) -> list[str]:
    names = list(ctx.update_field_names)
    if ctx.has_soft_delete:
        for n in ("deleted_at", "deleted_by"):
            if _model_has_field(ctx.model, n) and n not in names:
                names.append(n)
    return names


def _render_revert_service_py(ctx: ScaffoldContext, es: str) -> str:
    revert_fields = _revert_model_update_field_names(ctx)
    fields_lit = ", ".join(f'"{n}"' for n in revert_fields)
    update_lines: list[str] = []
    for item in _service_ordered_field_items(ctx):
        if isinstance(item, ForeignKeySpec):
            fk = item
            update_lines.append(f'    update_data["{fk.name}_id"] = getattr(snapshot, "{fk.name}_id", None)')
        else:
            spec = item
            f = spec.django_field
            if getattr(f, "auto_now", False) or getattr(f, "auto_now_add", False):
                continue
            update_lines.append(f'    update_data["{spec.name}"] = getattr(snapshot, "{spec.name}")')
    if ctx.has_soft_delete and _model_has_field(ctx.model, "deleted_at"):
        update_lines.append('    update_data["deleted_at"] = getattr(snapshot, "deleted_at", None)')
    if ctx.has_soft_delete and _model_has_field(ctx.model, "deleted_by"):
        update_lines.append('    update_data["deleted_by_id"] = getattr(snapshot, "deleted_by_id", None)')
    resolve_fk_lines = [
        f'    resolve_fk(update_data, "{item.name}", {item.related_model.__name__})'
        for item in ctx.ordered_fields
        if isinstance(item, ForeignKeySpec)
    ]
    deleted_by_block = ""
    if _model_has_field(ctx.model, "deleted_by"):
        deleted_by_block = """    deleted_by_id = update_data.pop("deleted_by_id", None)
    if deleted_by_id:
        update_data["deleted_by"] = get_object(User, id=deleted_by_id)
    else:
        update_data["deleted_by"] = None
"""
    auth_action_revert = f"{ctx.app_label}:{ctx.model_name.lower()}:history:revert"
    return f"""


@transaction.atomic
def {es}_revert_to_history(
    *,
    id: UUID,
    history_id: int,
    requesting_user: User,
) -> {ctx.model_name}:
    instance = get_authorized_object(
        queryset={ctx.model_name}.objects.all(),
        user=requesting_user,
        action="{auth_action_revert}",
        resource_code=_RESOURCE_CODE,
        resource_identifier=str(id),
        id=id,
    )
    {ctx.historical_model_name} = apps.get_model("{ctx.app_label}", "{ctx.historical_model_name}")
    historical = get_object({ctx.historical_model_name}, id=id, history_id=history_id)
    snapshot = historical.instance

    update_data: Dict[str, Any] = {{}}
{chr(10).join(update_lines)}
{chr(10).join(resolve_fk_lines)}
{deleted_by_block}
    instance, _ = model_update(
        instance=instance,
        fields=[{fields_lit}],
        data=update_data,
    )

    _invalidate_list_cache()
    return instance
"""


def _collect_dep_model_imports(dependents: list[DependentSpec]) -> list[tuple[str, str]]:
    """Return (module, classname) for every child model in the dep tree (recursively)."""
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for dep in dependents:
        if dep.is_reference_domain_resource:
            continue
        key = (_top_pkg(dep.child_model.__module__), dep.child_model.__name__)
        if key not in seen:
            seen.add(key)
            out.append(key)
        for t in _collect_dep_model_imports(dep.children):
            if t not in seen:
                seen.add(t)
                out.append(t)
    return out


def _nested_spec_constant_name(dep: DependentSpec) -> str:
    """Stable module-level constant name for a dependent's ``NestedSpec`` tuple."""
    return f"_{dep.accessor.upper()}_NESTED"


def _format_str_tuple_literal(names: list[str]) -> str:
    """Render ``names`` as a Python tuple literal string (single-element gets trailing comma)."""
    if not names:
        return "()"
    if len(names) == 1:
        return f'("{names[0]}",)'
    items = ", ".join(f'"{n}"' for n in names)
    return f"({items})"


def _render_nested_spec_literal_lines(sub: DependentSpec, *, indent: str) -> list[str]:
    """Render a single ``NestedSpec(...)`` literal for ``sub`` as indented lines."""
    key = _dep_datatype_sub_api_key(sub)
    lines: list[str] = [f"{indent}NestedSpec("]
    lines.append(f'{indent}    key="{key}",')
    lines.append(f"{indent}    model={sub.child_model.__name__},")
    lines.append(f'{indent}    parent_field="{sub.parent_fk_name}",')
    lines.append(f"{indent}    many={'True' if sub.is_many else 'False'},")
    if key != sub.accessor:
        lines.append(f'{indent}    related_accessor="{sub.accessor}",')
    if sub.child_m2m:
        m2m_names = [m.name for m in sub.child_m2m]
        lines.append(f"{indent}    m2m_fields={_format_str_tuple_literal(m2m_names)},")
    if sub.children:
        lines.append(f"{indent}    nested=(")
        for sub_sub in sub.children:
            lines.extend(_render_nested_spec_literal_lines(sub_sub, indent=indent + "        "))
        lines.append(f"{indent}    ),")
    lines.append(f"{indent}),")
    return lines


def _render_nested_spec_constants(dependents: list[DependentSpec]) -> str:
    """Emit module-level ``NestedSpec`` tuples for dependents that have sub-children."""
    blocks: list[str] = []
    for dep in dependents:
        if dep.is_reference_domain_resource:
            continue
        if not dep.children:
            continue
        const_name = _nested_spec_constant_name(dep)
        lines: list[str] = [f"{const_name}: tuple[NestedSpec, ...] = ("]
        for sub in dep.children:
            lines.extend(_render_nested_spec_literal_lines(sub, indent="    "))
        lines.append(")")
        blocks.append("\n".join(lines))
    return "\n\n\n".join(blocks)


def _render_dep_helper_call(dep: DependentSpec, *, mode: str) -> str:
    """Render a ``children_create`` / ``children_replace`` / ``one_to_one_upsert`` call for ``dep``.

    ``mode`` is ``"create"`` (uses the create-path parameter name as the payload)
    or ``"replace"`` (uses ``_<accessor>_data`` popped from the update payload).
    """
    m2m_names = [m.name for m in dep.child_m2m]
    m2m_literal = _format_str_tuple_literal(m2m_names) if m2m_names else None
    nested_ref = _nested_spec_constant_name(dep) if dep.children else None
    child_cls = dep.child_model.__name__

    def _body(kwargs: list[tuple[str, str]]) -> list[str]:
        out = []
        for k, v in kwargs:
            out.append(f"        {k}={v},")
        if m2m_literal:
            out.append(f"        m2m_fields={m2m_literal},")
        if nested_ref:
            out.append(f"        nested={nested_ref},")
        return out

    if dep.is_many:
        if mode == "create":
            lines = ["    children_create("]
            lines.extend(
                _body([
                    ("model", child_cls),
                    ("parent_field", f'"{dep.parent_fk_name}"'),
                    ("parent", "instance"),
                    ("items", dep.accessor),
                ])
            )
            lines.append("    )")
            return "\n".join(lines)
        lines = ["    children_replace("]
        lines.extend(
            _body([
                ("manager", f"instance.{dep.accessor}"),
                ("model", child_cls),
                ("parent_field", f'"{dep.parent_fk_name}"'),
                ("parent", "instance"),
                ("items", f"_{dep.accessor}_data"),
            ])
        )
        lines.append("    )")
        return "\n".join(lines)

    # one-to-one / single-child
    data_arg = dep.accessor if mode == "create" else f"_{dep.accessor}_data"
    lines = ["    one_to_one_upsert("]
    lines.extend(
        _body([
            ("related_accessor", f'"{dep.accessor}"'),
            ("model", child_cls),
            ("parent_field", f'"{dep.parent_fk_name}"'),
            ("parent", "instance"),
            ("data", data_arg),
        ])
    )
    lines.append("    )")
    return "\n".join(lines)


def _render_dep_create_service_block(dependents: list[DependentSpec]) -> str:
    """Render the nested-child creation block that goes after instance.save() in _create."""
    if not dependents:
        return ""
    return "\n".join(
        _render_dep_helper_call(dep, mode="create") for dep in dependents if not dep.is_reference_domain_resource
    )


def _render_dep_update_service_block(dependents: list[DependentSpec]) -> tuple[str, str]:
    """
    Return ``(pop_block, replace_block)``.

    - ``pop_block``: lines that pop each dependent's payload from ``data`` before
      ``model_update``.
    - ``replace_block``: helper calls (``children_replace`` / ``one_to_one_upsert``)
      that recreate / upsert the child rows after ``model_update``.

    The replace helpers handle both many (reverse FK) and one-to-one relations
    uniformly, including any nested sub-children declared in the module-level
    ``NestedSpec`` constant emitted for this dependent.
    """
    if not dependents:
        return "", ""
    filtered = [dep for dep in dependents if not dep.is_reference_domain_resource]
    pop_lines = [f'    _{dep.accessor}_data = data.pop("{dep.accessor}", None)' for dep in filtered]
    replace_blocks = [_render_dep_helper_call(dep, mode="replace") for dep in filtered]
    return "\n".join(pop_lines), "\n".join(replace_blocks)


def render_services_py(ctx: ScaffoldContext) -> str:
    es = _entity_snake(ctx.model_name)
    model_path = f"{ctx.app_python_path}.models"

    any_many_dep = any(dep.is_many for dep in ctx.dependents)
    any_one_dep = any(not dep.is_many for dep in ctx.dependents)
    any_nested_constant = any(bool(dep.children) and not dep.is_reference_domain_resource for dep in ctx.dependents)
    need_m2m_helper = bool(ctx.m2m_fields)

    services_imports: list[str] = ["model_update"]
    if any_nested_constant:
        services_imports.append("NestedSpec")
    if any_many_dep:
        services_imports.extend(["children_create", "children_replace"])
    if any_one_dep:
        services_imports.append("one_to_one_upsert")
    if need_m2m_helper:
        services_imports.append("m2m_set_if_given")
    services_import_names = sorted(set(services_imports))

    if len(services_import_names) == 1:
        services_import_line = f"from core.common.services import {services_import_names[0]}"
    else:
        services_import_line = (
            "from core.common.services import (\n" + "\n".join(f"    {name}," for name in services_import_names) + "\n)"
        )

    import_lines: list[str] = [
        "from typing import Any, Dict",
        "from uuid import UUID",
        "",
        "from django.db import transaction",
        "",
        "from core.security.services import authorize, get_authorized_object",
        services_import_line,
        "from core.common.utils import get_object, invalidate_list_cache, resolve_fk",
        f"from {model_path} import {ctx.model_name}",
    ]
    if ctx.with_history_extras:
        import_lines.insert(3, "from django.apps import apps")
        import_lines.insert(4, "")
    for mod, cls in sorted(set(ctx.fk_imports), key=lambda t: (t[0], t[1])):
        line = f"from {mod} import {cls}"
        if line not in import_lines:
            import_lines.append(line)
    if not any(cls == "User" for _, cls in ctx.fk_imports):
        import_lines.append("from core.users.models import User")
    # Import child models for dependents
    for mod, cls in _collect_dep_model_imports(ctx.dependents):
        line = f"from {mod} import {cls}"
        if line not in import_lines:
            import_lines.append(line)
    create_params: list[str] = []
    for item in _service_ordered_field_items(ctx):
        if isinstance(item, ForeignKeySpec):
            fk = item
            if _fk_related_is_content_type(fk):
                if fk.required:
                    create_params.append(f"    {fk.name}_id: int,")
                else:
                    create_params.append(f"    {fk.name}_id: int | None = None,")
            elif fk.required:
                create_params.append(f"    {fk.name}_id: UUID,")
            else:
                create_params.append(f"    {fk.name}_id: UUID | None = None,")
        else:
            spec = item
            f = spec.django_field
            if getattr(f, "auto_now", False) or getattr(f, "auto_now_add", False):
                continue
            py_t = "str"
            if isinstance(f, ArrayField):
                py_t = _postgres_array_python_type_annotation(f)
            elif isinstance(f, models.BooleanField):
                py_t = "bool"
            elif isinstance(f, models.IntegerField):
                py_t = "int"
            elif isinstance(f, models.UUIDField):
                py_t = "UUID"
            elif isinstance(f, models.DateTimeField):
                py_t = "Any | None"
            elif isinstance(f, models.DateField):
                py_t = "Any | None"
            elif isinstance(f, (models.DecimalField, models.FloatField)):
                py_t = "Any"
            elif isinstance(f, models.JSONField):
                py_t = "Any"
            if f.has_default() and not callable(f.default):
                create_params.append(f"    {spec.name}: {py_t} = {f.default!r},")
                continue
            if f.null and not isinstance(f, models.BooleanField):
                create_params.append(f"    {spec.name}: {py_t} | None = None,")
            elif not _is_required_for_create(f):
                if py_t == "str":
                    create_params.append(f"    {spec.name}: str | None = None,")
                elif py_t == "bool":
                    create_params.append(f"    {spec.name}: bool | None = None,")
                else:
                    create_params.append(f"    {spec.name}: {py_t} | None = None,")
            else:
                create_params.append(f"    {spec.name}: {py_t},")

    resolve_lines = []
    for item in _service_ordered_field_items(ctx):
        if isinstance(item, ForeignKeySpec):
            fk = item
            rel = fk.related_model.__name__
            if fk.required:
                resolve_lines.append(f"    {fk.name} = get_object({rel}, id={fk.name}_id)")
            else:
                resolve_lines.append(f"    {fk.name} = get_object({rel}, id={fk.name}_id) if {fk.name}_id else None")

    model_kwargs = []
    for item in _service_ordered_field_items(ctx):
        if isinstance(item, ForeignKeySpec):
            fk = item
            model_kwargs.append(f"        {fk.name}={fk.name},")
        else:
            spec = item
            f = spec.django_field
            if getattr(f, "auto_now", False) or getattr(f, "auto_now_add", False):
                continue
            if isinstance(f, ArrayField):
                if f.null:
                    model_kwargs.append(f"        {spec.name}={spec.name},")
                elif not _is_required_for_create(f):
                    model_kwargs.append(f"        {spec.name}={spec.name} if {spec.name} is not None else [],")
                else:
                    model_kwargs.append(f"        {spec.name}={spec.name},")
            elif isinstance(f, (models.CharField, models.TextField)) and not f.null:
                model_kwargs.append(f'        {spec.name}={spec.name} or "",')
            else:
                model_kwargs.append(f"        {spec.name}={spec.name},")

    resolve_update = [
        f'    resolve_fk(update_data, "{item.name}", {item.related_model.__name__})'
        for item in ctx.ordered_fields
        if isinstance(item, ForeignKeySpec)
    ]

    fields_literal = ", ".join(f'"{n}"' for n in ctx.update_field_names)

    # Dependent params for _create signature
    dep_create_params: list[str] = []
    for dep in ctx.dependents:
        if dep.is_reference_domain_resource:
            continue
        if dep.is_many:
            dep_create_params.append(f"    {dep.accessor}: list[dict] | None = None,")
        else:
            dep_create_params.append(f"    {dep.accessor}: dict | None = None,")

    # M2M params for _create signature
    m2m_create_params = [f"    {fk.name}: list | None = None," for fk in ctx.m2m_fields]

    # Nested child creation block (after instance.save())
    dep_create_body = _render_dep_create_service_block(ctx.dependents)
    dep_create_section = f"\n{dep_create_body}" if dep_create_body.strip() else ""

    # M2M set() calls after instance.save() — delegated to m2m_set_if_given.
    m2m_create_lines: list[str] = [f'    m2m_set_if_given(instance, "{fk.name}", {fk.name})' for fk in ctx.m2m_fields]
    m2m_create_section = "\n" + "\n".join(m2m_create_lines) if m2m_create_lines else ""

    # Dependent data popping + replace-all blocks for _update
    dep_pop_block, dep_replace_block = _render_dep_update_service_block(ctx.dependents)
    dep_pop_section = f"\n{dep_pop_block}" if dep_pop_block.strip() else ""
    dep_replace_section = f"\n{dep_replace_block}" if dep_replace_block.strip() else ""

    # M2M pop + m2m_set_if_given for _update
    m2m_update_pop_lines: list[str] = [f'    _{fk.name}_ids = data.pop("{fk.name}", None)' for fk in ctx.m2m_fields]
    m2m_update_set_lines: list[str] = [
        f'    m2m_set_if_given(instance, "{fk.name}", _{fk.name}_ids)' for fk in ctx.m2m_fields
    ]
    m2m_pop_section = "\n" + "\n".join(m2m_update_pop_lines) if m2m_update_pop_lines else ""
    m2m_set_section = "\n" + "\n".join(m2m_update_set_lines) if m2m_update_set_lines else ""

    # Module-level NestedSpec constants shared between create and replace helper calls.
    nested_spec_block = _render_nested_spec_constants(ctx.dependents)
    nested_spec_section = f"\n\n{nested_spec_block}\n" if nested_spec_block else ""

    # Combine all create params
    all_create_params = create_params + m2m_create_params + dep_create_params

    import_block = "\n".join(import_lines).strip() + "\n"
    resource_code = ctx.model_name
    svc_cache_ns = f"{es}:list"
    auth_action_create = f"{ctx.app_label}:{ctx.model_name.lower()}:create"
    auth_action_update = f"{ctx.app_label}:{ctx.model_name.lower()}:update"
    auth_action_delete = f"{ctx.app_label}:{ctx.model_name.lower()}:delete"
    auth_action_restore = f"{ctx.app_label}:{ctx.model_name.lower()}:restore"
    auth_action_hard_delete = f"{ctx.app_label}:{ctx.model_name.lower()}:hard_delete"

    soft_delete_service_block = ""
    if ctx.has_soft_delete:
        soft_delete_service_block = f"""

@transaction.atomic
def {es}_delete(
    *,
    id: UUID,
    requesting_user: User,
) -> None:
    instance = get_authorized_object(
        queryset={ctx.model_name}.objects.all(),
        user=requesting_user,
        action="{auth_action_delete}",
        resource_code=_RESOURCE_CODE,
        resource_identifier=str(id),
        id=id,
    )
    instance.delete(user=requesting_user)
    _invalidate_list_cache()


@transaction.atomic
def {es}_restore(
    *,
    id: UUID,
    requesting_user: User,
) -> {ctx.model_name}:
    instance = get_authorized_object(
        queryset={ctx.model_name}.objects.all(),
        user=requesting_user,
        action="{auth_action_restore}",
        resource_code=_RESOURCE_CODE,
        resource_identifier=str(id),
        id=id,
    )
    instance.restore(user=requesting_user)
    _invalidate_list_cache()
    return instance


@transaction.atomic
def {es}_hard_delete(
    *,
    id: UUID,
    requesting_user: User,
) -> None:
    instance = get_authorized_object(
        queryset={ctx.model_name}.objects.all(),
        user=requesting_user,
        action="{auth_action_hard_delete}",
        resource_code=_RESOURCE_CODE,
        resource_identifier=str(id),
        id=id,
    )
    instance.hard_delete()
    _invalidate_list_cache()
"""

    text = (
        f"""{import_block}

_RESOURCE_CODE = "{resource_code}"
_LIST_CACHE_NS = "{svc_cache_ns}"
{nested_spec_section}

def _invalidate_list_cache() -> None:
    transaction.on_commit(lambda: invalidate_list_cache(_LIST_CACHE_NS))


@transaction.atomic
def {es}_create(
    *,
{chr(10).join(all_create_params)}
    requesting_user: User,
) -> {ctx.model_name}:
    authorize(
        user=requesting_user,
        action="{auth_action_create}",
        resource_code=_RESOURCE_CODE,
    )
{chr(10).join(resolve_lines)}
    instance = {ctx.model_name}(
{chr(10).join(model_kwargs)}
    )
    instance.full_clean()
    instance.save()
{m2m_create_section}{dep_create_section}
    _invalidate_list_cache()
    return instance


@transaction.atomic
def {es}_update(
    *,
    id: UUID,
    data: Dict[str, Any],
    requesting_user: User,
) -> {ctx.model_name}:
    instance = get_authorized_object(
        queryset={ctx.model_name}.objects.all(),
        user=requesting_user,
        action="{auth_action_update}",
        resource_code=_RESOURCE_CODE,
        resource_identifier=str(id),
        id=id,
    )
{m2m_pop_section}{dep_pop_section}
    update_data: Dict[str, Any] = {{**data}}
{chr(10).join(resolve_update)}

    instance, _ = model_update(
        instance=instance,
        fields=[{fields_literal}],
        data=update_data,
    )
{m2m_set_section}{dep_replace_section}
    _invalidate_list_cache()
    return instance
"""
        + soft_delete_service_block
    )
    if ctx.with_history_extras:
        text += _render_revert_service_py(ctx, es)
    return text


def _selectors_select_related_names(ctx: ScaffoldContext) -> list[str]:
    """FK relation names to pass to ``select_related`` for list/detail output serializers.

    Output compact serializers read ``instance.<fk.name>`` (the related row), not
    ``instance.<fk.name>_id``. List and detail querysets must join these relations.
    """
    names = [fk.name for fk in ctx.foreign_keys]
    if _model_has_field(ctx.model, "deleted_by") and "deleted_by" not in names:
        names.append("deleted_by")
    return names


def _selectors_detail_fn(ctx: ScaffoldContext, es: str) -> str:
    rel_names = _selectors_select_related_names(ctx)
    if rel_names:
        sr = ", ".join(f'"{name}"' for name in rel_names)
        qs_expr = f"{ctx.model_name}.objects.select_related({sr})"
    else:
        qs_expr = f"{ctx.model_name}.objects.all()"
    # Add prefetch_related for cascade-owned dependents to avoid N+1
    prefetch_accessors = [f'"{dep.accessor}"' for dep in ctx.dependents]
    if prefetch_accessors:
        pf = ", ".join(prefetch_accessors)
        qs_expr = f"{qs_expr}.prefetch_related({pf})"
    auth_prefix = f"{ctx.app_label}:{ctx.model_name.lower()}"
    return f"""
def get_{es}(*, id: UUID, requesting_user: User) -> {ctx.model_name}:
    instance = get_authorized_object(
        queryset={qs_expr},
        user=requesting_user,
        action="{auth_prefix}:retrieve",
        resource_code=_RESOURCE_CODE,
        resource_identifier=str(id),
        id=id,
    )
    instance.revision = revision_payload_for_latest(instance)  # type: ignore[attr-defined]
    return instance
"""


def _selectors_history_extras_fn(ctx: ScaffoldContext, es: str) -> str:
    auth_prefix = f"{ctx.app_label}:{ctx.model_name.lower()}"
    return f"""


def get_{es}_history_previous_record(*, id: UUID, history_id: int, requesting_user: User):
    get_authorized_object(
        queryset={ctx.model_name}.objects.all(),
        user=requesting_user,
        action="{auth_prefix}:history:retrieve",
        resource_code=_RESOURCE_CODE,
        resource_identifier=str(id),
        id=id,
    )
    record = _get_{es}_history_record_unchecked(id=id, history_id=history_id)
    return record.prev_record


def get_{es}_history_next_record(*, id: UUID, history_id: int, requesting_user: User):
    get_authorized_object(
        queryset={ctx.model_name}.objects.all(),
        user=requesting_user,
        action="{auth_prefix}:history:retrieve",
        resource_code=_RESOURCE_CODE,
        resource_identifier=str(id),
        id=id,
    )
    record = _get_{es}_history_record_unchecked(id=id, history_id=history_id)
    return record.next_record


def get_{es}_history_diff(*, id: UUID, from_history_id: int, to_history_id: int, requesting_user: User):
    get_authorized_object(
        queryset={ctx.model_name}.objects.all(),
        user=requesting_user,
        action="{auth_prefix}:history:diff",
        resource_code=_RESOURCE_CODE,
        resource_identifier=str(id),
        id=id,
    )
    old = _get_{es}_history_record_unchecked(id=id, history_id=from_history_id)
    new = _get_{es}_history_record_unchecked(id=id, history_id=to_history_id)
    return new.diff_against(old)
"""


def _selectors_crud_audit_fn(ctx: ScaffoldContext, es: str) -> str:
    auth_prefix = f"{ctx.app_label}:{ctx.model_name.lower()}"
    return f"""


def _{es}_content_type() -> ContentType:
    return ContentType.objects.get_for_model({ctx.model_name})


def get_{es}_object_crud_events(
    *,
    id: UUID,
    filters: dict | None = None,
    requesting_user: User,
) -> QuerySet[CRUDEvent]:
    get_authorized_object(
        queryset={ctx.model_name}.objects.all(),
        user=requesting_user,
        action="{auth_prefix}:audit:object:list",
        resource_code=_RESOURCE_CODE,
        resource_identifier=str(id),
        id=id,
    )
    filters = filters or {{}}
    ct = _{es}_content_type()
    qs = CRUDEvent.objects.filter(content_type=ct, object_id=str(id)).select_related("content_type", "user")
    return CrudEventFilter(filters, qs).qs.order_by("-datetime", "-id")


def get_{es}_model_crud_events(
    *,
    filters: dict | None = None,
    requesting_user: User,
) -> QuerySet[CRUDEvent]:
    authorize(user=requesting_user, action="{auth_prefix}:audit:model:list", resource_code=_RESOURCE_CODE)
    filters = filters or {{}}
    ct = _{es}_content_type()
    qs = CRUDEvent.objects.filter(content_type=ct).select_related("content_type", "user")
    return CrudEventFilter(filters, qs).qs.order_by("-datetime", "-id")
"""


def render_selectors_py(ctx: ScaffoldContext) -> str:
    es = _entity_snake(ctx.model_name)
    plural = _plural_snake(ctx.resource_module)
    model_path = f"{ctx.app_python_path}.models"

    sel_resource_code = ctx.model_name
    sel_auth_prefix = f"{ctx.app_label}:{ctx.model_name.lower()}"
    security_imports = ["authorize_queryset", "get_authorized_object"]
    if ctx.with_crud_audit:
        security_imports.insert(0, "authorize")

    head_imports = [
        "from uuid import UUID",
        "",
    ]
    if ctx.has_history:
        head_imports.extend([
            "from django.apps import apps",
            "",
        ])
    head_imports.extend([
        "from django.db.models import QuerySet",
        "",
        f"from core.security.services import {', '.join(security_imports)}",
        "from core.users.models import User",
        "",
    ])
    if ctx.rich_serializers:
        head_imports.append("from core.common.utils import revision_payload_for_latest")
        head_imports.append("")
    if ctx.with_crud_audit:
        head_imports.extend([
            "from django.contrib.contenttypes.models import ContentType",
            "",
            "from easyaudit.models import CRUDEvent",
            "",
            "from core.api.filters import CrudEventFilter",
            "",
        ])
    head_imports.extend([
        "from core.common.utils import get_object",
        f"from {ctx.app_python_path}.filters import {ctx.filter_class_name}",
        f"from {model_path} import {ctx.model_name}",
        "",
        f'_RESOURCE_CODE = "{sel_resource_code}"',
        "",
    ])

    rel_names = _selectors_select_related_names(ctx)
    if rel_names:
        sr = ", ".join(f'"{name}"' for name in rel_names)
        list_qs_tail = f".select_related({sr})"
    else:
        list_qs_tail = ""
    list_fn_body = (
        f"def get_{plural}(*, filters: dict | None = None, requesting_user: User) -> QuerySet[{ctx.model_name}]:\n"
        f"    filters = filters or {{}}\n"
        f"    qs = authorize_queryset(\n"
        f"        queryset={ctx.model_name}.objects.all(),\n"
        f"        user=requesting_user,\n"
        f'        action="{sel_auth_prefix}:list",\n'
        f"        resource_code=_RESOURCE_CODE,\n"
        f"    )\n"
        f"    return {ctx.filter_class_name}(filters, qs).qs{list_qs_tail}"
    )

    bare_retrieve = (
        ""
        if ctx.rich_serializers
        else f"""

def get_{es}(*, id: UUID, requesting_user: User) -> {ctx.model_name}:
    return get_authorized_object(
        queryset={ctx.model_name}.objects.all(),
        user=requesting_user,
        action="{sel_auth_prefix}:retrieve",
        resource_code=_RESOURCE_CODE,
        resource_identifier=str(id),
        id=id,
    )
"""
    )

    body = f"""{chr(10).join(head_imports)}
{list_fn_body}
{bare_retrieve}"""

    if ctx.rich_serializers:
        body += _selectors_detail_fn(ctx, es)

    if ctx.has_history:
        body += f"""
def get_{es}_history(*, id: UUID, requesting_user: User) -> QuerySet:
    \"\"\"Return historical rows for this {ctx.model_name}, newest first.\"\"\"
    get_authorized_object(
        queryset={ctx.model_name}.objects.all(),
        user=requesting_user,
        action="{sel_auth_prefix}:history:list",
        resource_code=_RESOURCE_CODE,
        resource_identifier=str(id),
        id=id,
    )
    {ctx.historical_model_name} = apps.get_model("{ctx.app_label}", "{ctx.historical_model_name}")
    return {ctx.historical_model_name}.objects.filter(id=id).order_by("-history_date", "-history_id")


def _get_{es}_history_record_unchecked(*, id: UUID, history_id: int):
    {ctx.historical_model_name} = apps.get_model("{ctx.app_label}", "{ctx.historical_model_name}")
    return get_object({ctx.historical_model_name}, id=id, history_id=history_id)


def get_{es}_history_record(*, id: UUID, history_id: int, requesting_user: User):
    \"\"\"Return a single historical row.\"\"\"
    get_authorized_object(
        queryset={ctx.model_name}.objects.all(),
        user=requesting_user,
        action="{sel_auth_prefix}:history:retrieve",
        resource_code=_RESOURCE_CODE,
        resource_identifier=str(id),
        id=id,
    )
    return _get_{es}_history_record_unchecked(id=id, history_id=history_id)
"""

    if ctx.with_history_extras:
        body += _selectors_history_extras_fn(ctx, es)
    if ctx.with_crud_audit:
        body += _selectors_crud_audit_fn(ctx, es)

    return body


def render_filters_py(ctx: ScaffoldContext) -> str:
    ordering_pairs = _order_by_filter_pairs()

    visible_line = ""
    if ctx.has_visible:
        visible_line = '    is_visible = django_filters.BooleanFilter(field_name="is_visible", lookup_expr="exact")\n'

    fk_lines = []
    content_type_filter_method_lines: list[str] = []
    char_lines = []
    if ctx.reference_id_field is not None:
        char_lines.append('    reference_id = django_filters.CharFilter(lookup_expr="icontains")')
    for item in ctx.ordered_fields:
        if isinstance(item, ForeignKeySpec):
            if _fk_related_is_content_type(item):
                fk_lines.append(f'    {item.name} = django_filters.CharFilter(method="filter_{item.name}_natural_key")')
                content_type_filter_method_lines.extend([
                    f"    def filter_{item.name}_natural_key(self, queryset, name, value):",
                    "        try:",
                    "            content_type = content_type_from_natural_key(natural_key=value)",
                    "        except ValidationError:",
                    "            return queryset.none()",
                    f"        return queryset.filter({item.name}_id=content_type.id)",
                    "",
                ])
            else:
                fk_lines.append(f'    {item.name}_id = django_filters.UUIDFilter(field_name="{item.name}_id")')
                if _fk_related_is_terminology_concept(item):
                    fk_lines.append(
                        f'    {item.name}_code = django_filters.CharFilter(field_name="{item.name}__code", lookup_expr="icontains")'
                    )
        elif isinstance(item.django_field, (models.CharField, models.TextField)):
            char_lines.append(f'    {item.name} = django_filters.CharFilter(lookup_expr="icontains")')

    is_deleted_filter = ""
    if ctx.has_soft_delete:
        is_deleted_filter = """    is_deleted = django_filters.BooleanFilter(
        field_name="deleted_at", lookup_expr="isnull", exclude=True
    )
"""

    content_type_imports = ""
    if content_type_filter_method_lines:
        content_type_imports = "from django.core.exceptions import ValidationError\nfrom core.common.utils import content_type_from_natural_key\n\n"

    return f"""\
import django_filters
{content_type_imports}

from {ctx.app_python_path}.models import {ctx.model_name}


class {ctx.filter_class_name}(django_filters.FilterSet):
{visible_line}{is_deleted_filter}{chr(10).join(fk_lines)}
{chr(10).join(char_lines)}
{chr(10).join(content_type_filter_method_lines)}
    order_by = django_filters.OrderingFilter(
        fields=[
{chr(10).join(ordering_pairs)}
        ],
    )

    class Meta:
        model = {ctx.model_name}
        fields = []
"""


def _urls_api_import_names(ctx: ScaffoldContext) -> list[str]:
    m = ctx.model_name
    names = [
        f"{m}BulkCreateApi",
        f"{m}BulkUpdateApi",
    ]
    if ctx.has_soft_delete:
        names.append(f"{m}BulkDeleteApi")
    names.extend([
        f"{m}CreateApi",
        f"{m}ListApi",
    ])
    if ctx.with_crud_audit:
        names.append(f"{m}ModelCrudAuditListApi")
    names.append(f"{m}DetailApi")
    if ctx.has_history:
        if ctx.with_history_extras:
            names.extend([
                f"{m}HistoryDiffApi",
                f"{m}HistoryListApi",
                f"{m}HistoryPreviousApi",
                f"{m}HistoryNextApi",
                f"{m}HistoryRevertApi",
                f"{m}HistoryDetailApi",
            ])
        else:
            names.extend([
                f"{m}HistoryListApi",
                f"{m}HistoryDetailApi",
            ])
    if ctx.with_crud_audit:
        names.append(f"{m}ObjectCrudAuditListApi")
    names.append(f"{m}UpdateApi")
    if ctx.has_soft_delete:
        names.extend([
            f"{m}DeleteApi",
            f"{m}RestoreApi",
            f"{m}HardDeleteApi",
        ])
    return names


def render_urls_py(ctx: ScaffoldContext) -> str:
    patterns_var = ctx.url_prefix.replace("-", "_").replace("/", "_").strip("_") + "_patterns"
    if patterns_var[0].isdigit():
        patterns_var = "resource_" + patterns_var
    url_slug = ctx.resource_module.replace("_", "-")
    m = ctx.model_name

    imports = _urls_api_import_names(ctx)
    import_block = ",\n    ".join(imports)

    paths: list[str] = [
        f'    path("create/", {m}CreateApi.as_view(), name="{url_slug}-create"),',
        f'    path("bulk-create/", {m}BulkCreateApi.as_view(), name="{url_slug}-bulk-create"),',
        f'    path("bulk-update/", {m}BulkUpdateApi.as_view(), name="{url_slug}-bulk-update"),',
    ]
    if ctx.has_soft_delete:
        paths.append(f'    path("bulk-delete/", {m}BulkDeleteApi.as_view(), name="{url_slug}-bulk-delete"),')
    paths.append(f'    path("list/", {m}ListApi.as_view(), name="{url_slug}-list"),')
    if ctx.with_crud_audit:
        paths.append(
            f'    path("audit/", {m}ModelCrudAuditListApi.as_view(), name="{url_slug}-model-crud-audit-list"),'
        )
    paths.append(f'    path("<uuid:id>/", {m}DetailApi.as_view(), name="{url_slug}-detail"),')
    if ctx.has_history:
        if ctx.with_history_extras:
            paths.extend([
                f'    path("<uuid:id>/history/diff/", {m}HistoryDiffApi.as_view(), name="{url_slug}-history-diff"),',
                f'    path("<uuid:id>/history/", {m}HistoryListApi.as_view(), name="{url_slug}-history-list"),',
                f'    path("<uuid:id>/history/<int:history_id>/previous/", {m}HistoryPreviousApi.as_view(), name="{url_slug}-history-previous"),',
                f'    path("<uuid:id>/history/<int:history_id>/next/", {m}HistoryNextApi.as_view(), name="{url_slug}-history-next"),',
                f'    path("<uuid:id>/history/<int:history_id>/revert/", {m}HistoryRevertApi.as_view(), name="{url_slug}-history-revert"),',
                f'    path("<uuid:id>/history/<int:history_id>/", {m}HistoryDetailApi.as_view(), name="{url_slug}-history-detail"),',
            ])
        else:
            paths.extend([
                f'    path("<uuid:id>/history/", {m}HistoryListApi.as_view(), name="{url_slug}-history-list"),',
                f'    path("<uuid:id>/history/<int:history_id>/", {m}HistoryDetailApi.as_view(), name="{url_slug}-history-detail"),',
            ])
    if ctx.with_crud_audit:
        paths.append(
            f'    path("<uuid:id>/audit/", {m}ObjectCrudAuditListApi.as_view(), name="{url_slug}-object-crud-audit-list"),'
        )
    paths.append(f'    path("<uuid:id>/update/", {m}UpdateApi.as_view(), name="{url_slug}-update"),')
    if ctx.has_soft_delete:
        paths.extend([
            f'    path("<uuid:id>/delete/", {m}DeleteApi.as_view(), name="{url_slug}-delete"),',
            f'    path("<uuid:id>/restore/", {m}RestoreApi.as_view(), name="{url_slug}-restore"),',
            f'    path("<uuid:id>/hard-delete/", {m}HardDeleteApi.as_view(), name="{url_slug}-hard-delete"),',
        ])

    paths_joined = "\n".join(paths)
    return f"""\
from django.urls import include, path

from {ctx.app_python_path}.apis.{ctx.resource_module} import (
    {import_block},
)

app_name = "{ctx.app_url_namespace}"

{patterns_var} = [
{paths_joined}
]

urlpatterns = [
    path("{ctx.url_prefix}/", include({patterns_var})),
]
"""


def collect_generated_files(ctx: ScaffoldContext, *, app_dir: Path) -> dict[Path, str]:
    """Map absolute path -> file content (per-resource modules only)."""
    out: dict[Path, str] = {}
    out[app_dir / "apis" / f"{ctx.resource_module}.py"] = render_apis_py(ctx)
    out[app_dir / "services" / f"{ctx.resource_module}.py"] = render_services_py(ctx)
    out[app_dir / "selectors" / f"{ctx.resource_module}.py"] = render_selectors_py(ctx)
    return out


def api_export_names(ctx: ScaffoldContext) -> list[str]:
    """APIView class names to export from ``apis`` package (matches ``urls`` imports)."""
    return _urls_api_import_names(ctx)


def service_export_names(ctx: ScaffoldContext, entity_snake: str) -> list[str]:
    names = [
        f"{entity_snake}_create",
        f"{entity_snake}_update",
    ]
    if ctx.has_soft_delete:
        names.extend([
            f"{entity_snake}_delete",
            f"{entity_snake}_restore",
            f"{entity_snake}_hard_delete",
        ])
    if ctx.with_history_extras:
        names.insert(-1, f"{entity_snake}_revert_to_history")
    return names


def selector_export_names(ctx: ScaffoldContext, entity_snake: str, resource_module: str) -> list[str]:
    plural = _plural_snake(resource_module)
    names = [
        f"get_{entity_snake}",
        f"get_{plural}",
    ]
    if ctx.has_history:
        names.extend([
            f"get_{entity_snake}_history",
            f"get_{entity_snake}_history_record",
        ])
    if ctx.with_history_extras:
        names.extend([
            f"get_{entity_snake}_history_diff",
            f"get_{entity_snake}_history_next_record",
            f"get_{entity_snake}_history_previous_record",
        ])
    if ctx.with_crud_audit:
        names.extend([
            f"get_{entity_snake}_model_crud_events",
            f"get_{entity_snake}_object_crud_events",
        ])
    return names


def render_init_py(*, from_module: str, export_names: list[str]) -> str:
    imp = "from .{} import (\n{}\n)\n\n".format(
        from_module,
        ",\n".join(f"    {n}" for n in export_names) + ",",
    )
    all_lines = ",\n".join(f'    "{n}"' for n in export_names) + ",\n"
    return f"{imp}__all__ = [\n{all_lines}]\n"


def _format_standalone_all(export_names: list[str]) -> str:
    all_lines = ",\n".join(f'    "{n}"' for n in export_names) + ",\n"
    return f"__all__ = [\n{all_lines}]\n"


def _inject_into_all_section(all_section: str, new_names: list[str]) -> str:
    """Insert any names not already listed into the first __all__ = [ ... ] block."""
    eq = all_section.find("=")
    if eq == -1:
        return all_section
    lb = all_section.find("[", eq)
    if lb == -1:
        return all_section
    depth = 0
    i = lb
    while i < len(all_section):
        c = all_section[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                inner = all_section[lb + 1 : i]
                current = set(re.findall(r'"([^"]+)"', inner))
                to_add = [n for n in new_names if n not in current]
                if not to_add:
                    return all_section
                lines_to_add = "\n".join(f'    "{n}",' for n in to_add) + "\n"
                inner_body = inner.rstrip()
                if inner_body:
                    if not inner_body.endswith(","):
                        inner_body += ","
                    inner_body += "\n" + lines_to_add
                else:
                    inner_body = lines_to_add
                return all_section[: lb + 1] + "\n" + inner_body + all_section[i:]
        i += 1
    return all_section


def _inject_into_import_block(text: str, *, from_module: str, new_names: list[str]) -> str:
    """Insert any names not already listed into ``from .{from_module} import (...)``.

    Handles both ``from .x import a, b`` single-line form and the parenthesised
    multi-line form. Single-line imports are rewritten as multi-line to keep
    the output ruff-friendly. Returns ``text`` unchanged when the import block
    is not found or all ``new_names`` are already present.
    """

    pattern = re.compile(rf"from \.{re.escape(from_module)} import\s*(\(?)", re.MULTILINE)
    match = pattern.search(text)
    if match is None:
        return text

    open_paren = match.group(1)
    if open_paren == "(":
        lp = text.find("(", match.end() - 1)
        rp = text.find(")", lp)
        if rp == -1:
            return text
        inner = text[lp + 1 : rp]
        current = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", inner))
        to_add = [n for n in new_names if n not in current]
        if not to_add:
            return text
        lines_to_add = "\n".join(f"    {n}," for n in to_add) + "\n"
        body = inner.rstrip()
        if body:
            if not body.endswith(","):
                body += ","
            body += "\n" + lines_to_add
        else:
            body = "\n" + lines_to_add
        return text[: lp + 1] + body + text[rp:]

    line_end = text.find("\n", match.end())
    if line_end == -1:
        line_end = len(text)
    line_body = text[match.end() : line_end].strip()
    current = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", line_body))
    to_add = [n for n in new_names if n not in current]
    if not to_add:
        return text
    existing_names = [n.strip() for n in line_body.split(",") if n.strip()]
    all_names = existing_names + to_add
    rebuilt_inner = "\n".join(f"    {n}," for n in all_names)
    replacement = f"from .{from_module} import (\n{rebuilt_inner}\n)"
    return text[: match.start()] + replacement + text[line_end:]


OPENAPI_CONSTANTS_SECTION_HEADER = "# OpenAPI / drf-spectacular"


def merge_openapi_constant_into_constants(existing: str, ctx: ScaffoldContext) -> str:
    """
    Ensure constants.py defines ctx.openapi_tag_constant_name for drf-spectacular tags.
    Does not replace an existing assignment with the same name.
    """
    name = ctx.openapi_tag_constant_name
    if re.search(rf"^\s*{re.escape(name)}\s*=", existing, flags=re.MULTILINE):
        return existing
    literal = repr(ctx.openapi_tag_value)
    line = f"{name} = {literal}\n"
    if OPENAPI_CONSTANTS_SECTION_HEADER in existing:
        idx = existing.find(OPENAPI_CONSTANTS_SECTION_HEADER)
        line_end = existing.find("\n", idx)
        insert_at = len(existing) if line_end == -1 else line_end + 1
        return existing[:insert_at] + line + existing[insert_at:]
    sep = "\n\n" if existing.strip() else ""
    return existing.rstrip() + sep + f"{OPENAPI_CONSTANTS_SECTION_HEADER}\n{line}"


def merge_package_init_py(existing: str, *, from_module: str, export_names: list[str]) -> str:
    """
    Add or update package __init__.py: new `from .module import (...)` before __all__,
    and extend __all__ with any missing export names.
    """
    text = existing.rstrip()
    if not text:
        return render_init_py(from_module=from_module, export_names=export_names)

    import_mark = f"from .{from_module} import"
    has_import = import_mark in text

    if not has_import:
        import_block = "from .{} import (\n{}\n)\n".format(
            from_module,
            ",\n".join(f"    {n}" for n in export_names) + ",",
        )
        all_pos = text.find("__all__")
        if all_pos == -1:
            return text + "\n\n" + import_block + "\n" + _format_standalone_all(export_names)
        before = text[:all_pos].rstrip()
        after = text[all_pos:]
        merged_after = _inject_into_all_section(after, export_names)
        return before + "\n\n" + import_block + "\n\n" + merged_after + "\n"

    text = _inject_into_import_block(text, from_module=from_module, new_names=export_names)
    all_pos = text.find("__all__")
    if all_pos == -1:
        return text + "\n\n" + _format_standalone_all(export_names)
    return text[:all_pos] + _inject_into_all_section(text[all_pos:], export_names) + "\n"


def merge_filters_py(existing: str, ctx: ScaffoldContext) -> str:
    new_class = render_filters_py(ctx).strip()
    if f"class {ctx.filter_class_name}" in existing:
        raise ValueError(
            f"filters.py already defines {ctx.filter_class_name}. "
            "Remove it or choose another model; appending duplicate filter classes is not supported. "
            "Or pass --skip-filters to leave filters.py unchanged."
        )
    if existing.strip():
        return existing.rstrip() + "\n\n\n" + new_class + "\n"
    return new_class + "\n"


def merge_urls_py(existing: str, ctx: ScaffoldContext) -> str:
    if not existing.strip():
        return render_urls_py(ctx)
    raise ValueError(
        "urls.py is not empty; merge routes manually or back up the file. "
        f"Generated snippet uses prefix '{ctx.url_prefix}/'."
    )


def bulk_api_export_names(ctx: ScaffoldContext) -> list[str]:
    """API view class names emitted into ``apis/<resource>/bulk.py`` only."""
    m = ctx.model_name
    names = [f"{m}BulkCreateApi", f"{m}BulkUpdateApi"]
    if ctx.has_soft_delete:
        names.append(f"{m}BulkDeleteApi")
    return names


def bulk_serializer_export_names(ctx: ScaffoldContext) -> list[str]:
    """Serializer class names introduced by the bulk endpoints only."""
    return [f"{ctx.model_name}BulkUpdateItemInputSerializer"]


def merge_bulk_urls_py(existing: str, ctx: ScaffoldContext) -> str:
    """Inject the bulk url imports + ``path(...)`` rows into an existing ``urls.py``.

    Idempotent: if the bulk routes are already present the original text is
    returned unchanged. Raises ``ValueError`` if the existing file does not
    contain the resource's standard ``create/`` row to anchor the new entries.
    """

    m = ctx.model_name
    url_slug = ctx.resource_module.replace("_", "-")
    new_imports = bulk_api_export_names(ctx)
    if all(name in existing for name in new_imports):
        return existing

    import_anchor = f"    {m}CreateApi,"
    if import_anchor not in existing:
        raise ValueError(
            f"Could not locate '{import_anchor}' in urls.py imports. "
            "Add bulk imports manually or re-run without --only-bulk."
        )
    new_import_lines = "\n".join(f"    {name}," for name in new_imports if name not in existing)
    if new_import_lines:
        existing = existing.replace(import_anchor, f"{new_import_lines}\n{import_anchor}", 1)

    create_path_anchor = f'    path("create/", {m}CreateApi.as_view(), name="{url_slug}-create"),'
    if create_path_anchor not in existing:
        raise ValueError(
            f"Could not locate '{create_path_anchor}' in urls.py. "
            "Add bulk paths manually or re-run without --only-bulk."
        )
    bulk_path_lines = [
        f'    path("bulk-create/", {m}BulkCreateApi.as_view(), name="{url_slug}-bulk-create"),',
        f'    path("bulk-update/", {m}BulkUpdateApi.as_view(), name="{url_slug}-bulk-update"),',
    ]
    if ctx.has_soft_delete:
        bulk_path_lines.append(f'    path("bulk-delete/", {m}BulkDeleteApi.as_view(), name="{url_slug}-bulk-delete"),')
    bulk_path_lines = [line for line in bulk_path_lines if line not in existing]
    if bulk_path_lines:
        block = "\n".join(bulk_path_lines)
        existing = existing.replace(create_path_anchor, f"{create_path_anchor}\n{block}", 1)
    return existing
