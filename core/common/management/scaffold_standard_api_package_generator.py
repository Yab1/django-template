import ast
import re
from pathlib import Path

from core.common.management import scaffold_standard_api_generator as gen
from core.common.management import scaffold_standard_serializers_generator as ser_gen

_CLASS_RE = re.compile(r"^class\s+(\w+Api)\(AuthorizedAPIView\):", flags=re.MULTILINE)


def _split_rendered_api_module(rendered: str) -> tuple[str, dict[str, str]]:
    matches = list(_CLASS_RE.finditer(rendered))
    if not matches:
        raise ValueError("Generated API module did not contain any API classes.")

    imports = rendered[: matches[0].start()].rstrip() + "\n"
    class_blocks: dict[str, str] = {}

    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(rendered)
        class_name = match.group(1)
        class_blocks[class_name] = rendered[start:end].rstrip() + "\n"

    return imports, class_blocks


def _collect_used_names(class_blocks: list[str]) -> set[str]:
    tree = ast.parse("\n\n".join(class_blocks))
    used: set[str] = set()

    class UsedNameVisitor(ast.NodeVisitor):
        def visit_Name(self, node: ast.Name) -> None:  # noqa: N802
            if isinstance(node.ctx, ast.Load):
                used.add(node.id)
            self.generic_visit(node)

    UsedNameVisitor().visit(tree)
    return used


def _render_import_node(node: ast.stmt) -> str:
    return ast.unparse(node)


def _prune_imports(imports: str, class_blocks: list[str]) -> str:
    import_tree = ast.parse(imports)
    used_names = _collect_used_names(class_blocks)
    kept_imports: list[str] = []

    for node in import_tree.body:
        if isinstance(node, ast.Import):
            aliases = []
            for alias in node.names:
                binding = alias.asname or alias.name.split(".")[0]
                if binding in used_names:
                    aliases.append(alias)
            if aliases:
                kept_imports.append(_render_import_node(ast.Import(names=aliases)))
            continue

        if isinstance(node, ast.ImportFrom):
            if node.module == "__future__":
                kept_imports.append(_render_import_node(node))
                continue

            aliases = []
            for alias in node.names:
                binding = alias.asname or alias.name
                if binding in used_names:
                    aliases.append(alias)
            if aliases:
                kept_imports.append(
                    _render_import_node(ast.ImportFrom(module=node.module, names=aliases, level=node.level))
                )
            continue

        kept_imports.append(_render_import_node(node))

    return "\n".join(kept_imports).rstrip() + "\n"


def _render_api_module(imports: str, class_blocks: list[str]) -> str:
    pruned_imports = _prune_imports(imports, class_blocks)
    return pruned_imports.rstrip() + "\n\n\n" + "\n\n\n".join(block.rstrip() for block in class_blocks) + "\n"


def _api_module_export_map(ctx: gen.ScaffoldContext) -> dict[str, list[str]]:
    model_name = ctx.model_name

    crud_exports = [
        f"{model_name}CreateApi",
        f"{model_name}ListApi",
        f"{model_name}DetailApi",
        f"{model_name}UpdateApi",
    ]
    if ctx.has_soft_delete:
        crud_exports.extend([
            f"{model_name}DeleteApi",
            f"{model_name}RestoreApi",
            f"{model_name}HardDeleteApi",
        ])

    bulk_exports = [
        f"{model_name}BulkCreateApi",
        f"{model_name}BulkUpdateApi",
    ]
    if ctx.has_soft_delete:
        bulk_exports.append(f"{model_name}BulkDeleteApi")

    history_exports: list[str] = []
    if ctx.has_history:
        history_exports = [
            f"{model_name}HistoryListApi",
            f"{model_name}HistoryDetailApi",
        ]
        if ctx.with_history_extras:
            history_exports.extend([
                f"{model_name}HistoryPreviousApi",
                f"{model_name}HistoryNextApi",
                f"{model_name}HistoryDiffApi",
                f"{model_name}HistoryRevertApi",
            ])

    module_map: dict[str, list[str]] = {
        "crud": crud_exports,
        "bulk": bulk_exports,
        "history": history_exports,
        "audit": [],
    }

    if ctx.with_crud_audit:
        module_map["audit"].extend([
            f"{model_name}ObjectCrudAuditListApi",
            f"{model_name}ModelCrudAuditListApi",
        ])

    return module_map


def render_resource_api_package_init(ctx: gen.ScaffoldContext) -> str:
    content = ""
    for module_name, export_names in _api_module_export_map(ctx).items():
        if not export_names:
            continue
        content = gen.merge_package_init_py(content, from_module=module_name, export_names=export_names)
    return content


def collect_api_generated_files(ctx: gen.ScaffoldContext, *, app_dir: Path) -> dict[Path, str]:
    rendered = gen.render_apis_py(ctx)
    imports, class_blocks = _split_rendered_api_module(rendered)

    api_package_dir = app_dir / "apis" / ctx.resource_module
    files: dict[Path, str] = {
        api_package_dir / "__init__.py": render_resource_api_package_init(ctx),
    }

    grouped_names = _api_module_export_map(ctx)
    consumed_names: set[str] = set()

    for module_name in ("crud", "bulk", "history", "audit"):
        names = [name for name in grouped_names[module_name] if name in class_blocks]
        consumed_names.update(names)
        target = api_package_dir / f"{module_name}.py"
        if names:
            files[target] = _render_api_module(imports, [class_blocks[name] for name in names])

    leftover_names = [name for name in class_blocks if name not in consumed_names]
    if leftover_names:
        names = ", ".join(sorted(leftover_names))
        raise ValueError(
            f"Unmapped API classes for resource '{ctx.resource_module}': {names}. "
            "Add explicit grouping in scaffold_standard_api_package_generator.py."
        )

    return files


def collect_generated_files(ctx: gen.ScaffoldContext, *, app_dir: Path) -> dict[Path, str]:
    out = collect_api_generated_files(ctx, app_dir=app_dir)
    out.update(ser_gen.collect_generated_files(ctx, app_dir=app_dir))
    out[app_dir / "services" / f"{ctx.resource_module}.py"] = gen.render_services_py(ctx)
    out[app_dir / "selectors" / f"{ctx.resource_module}.py"] = gen.render_selectors_py(ctx)
    return out


def api_generated_paths(ctx: gen.ScaffoldContext, *, app_dir: Path) -> list[Path]:
    api_package_dir = app_dir / "apis" / ctx.resource_module
    return [
        api_package_dir / "__init__.py",
        api_package_dir / "crud.py",
        api_package_dir / "bulk.py",
        api_package_dir / "history.py",
        api_package_dir / "audit.py",
    ]


def collect_bulk_only_files(ctx: gen.ScaffoldContext, *, app_dir: Path) -> dict[Path, str]:
    """Return only the bulk API module file path/content for ``--only-bulk`` runs.

    Skips ``crud.py`` / ``history.py`` / ``audit.py`` and leaves the resource
    serializer / urls / package __init__ to be merged by the command. The
    returned ``bulk.py`` is sliced from the same rendered apis output that the
    full run uses so the file stays byte-identical between modes.
    """

    rendered = gen.render_apis_py(ctx)
    imports, class_blocks = _split_rendered_api_module(rendered)
    grouped_names = _api_module_export_map(ctx)
    bulk_names = [name for name in grouped_names["bulk"] if name in class_blocks]
    if not bulk_names:
        return {}
    target = app_dir / "apis" / ctx.resource_module / "bulk.py"
    return {target: _render_api_module(imports, [class_blocks[name] for name in bulk_names])}
