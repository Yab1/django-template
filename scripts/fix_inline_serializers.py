#!/usr/bin/env python3
"""
fix_inline_serializers.py

Moves inline Input/Output/QuerySerializer class definitions from API class bodies
into their corresponding serializer modules.

TRANSFORMATION
--------------
BEFORE (apis/quality_compliance.py):

    class ModalityQCLogCreateApi(AuthorizedAPIView):
        class InputSerializer(serializers.Serializer):
            schedule_id = serializers.UUIDField()

AFTER (apis/quality_compliance.py):

    from core.diagnostics.serializers.quality_compliance import (
        ModalityQCLogCreateInputSerializer,
    )

    class ModalityQCLogCreateApi(AuthorizedAPIView):
        InputSerializer = ModalityQCLogCreateInputSerializer

ADDED (serializers/quality_compliance.py):

    class ModalityQCLogCreateInputSerializer(serializers.Serializer):
        schedule_id = serializers.UUIDField()

NAMING RULE
-----------
    FooCreateApi.InputSerializer  →  FooCreateInputSerializer
    FooCreateApi.OutputSerializer →  FooCreateOutputSerializer
    FooListApi.QuerySerializer    →  FooListQuerySerializer

USAGE
-----
    # Dry run on single file
    python scripts/fix_inline_serializers.py core/notifications/apis/preferences.py --dry-run

    # Apply to single file
    python scripts/fix_inline_serializers.py core/notifications/apis/preferences.py

    # Dry run on directory
    python scripts/fix_inline_serializers.py core/notifications/apis/ --dry-run

    # Apply all files including history.py
    python scripts/fix_inline_serializers.py core/notifications/apis/

    # Skip history.py / audit.py files explicitly
    python scripts/fix_inline_serializers.py core/notifications/apis/ --skip-history
"""

import argparse
import re
import sys
from pathlib import Path

INLINE_SERIALIZER_NAMES = {"InputSerializer", "OutputSerializer", "QuerySerializer"}
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# File parsing
# ---------------------------------------------------------------------------


def _line_indent(line: str) -> int:
    """Return indentation depth; -1 for blank lines."""
    s = line.rstrip("\n")
    if not s.strip():
        return -1
    return len(s) - len(s.lstrip())


def _extract_class_block(lines: list[str], start: int) -> tuple[list[str], int]:
    """
    Extract the class block starting at `start` (including full body).
    Returns (class_lines, raw_end) where raw_end is the first line index
    NOT part of the class.
    """
    class_indent = _line_indent(lines[start])
    end = start + 1
    while end < len(lines):
        ind = _line_indent(lines[end])
        if ind == -1 or ind > class_indent:
            end += 1
        else:
            break

    # Trim trailing blank lines
    trim_end = end
    while trim_end > start + 1 and not lines[trim_end - 1].strip():
        trim_end -= 1

    return lines[start:trim_end], end


def _find_preceding_decorators(lines: list[str], class_idx: int) -> tuple[list[str], int]:
    """Walk backwards from class_idx to find @decorator lines at the same indent."""
    target_indent = _line_indent(lines[class_idx])
    decorators: list[str] = []
    i = class_idx - 1
    while i >= 0:
        s = lines[i].rstrip("\n")
        if not s.strip():
            break
        if _line_indent(lines[i]) == target_indent and s.lstrip().startswith("@"):
            decorators.insert(0, lines[i])
            i -= 1
        else:
            break
    return decorators, i + 1


def parse_api_file(filepath: Path) -> list[dict]:
    """
    Return info about every inline serializer class in an API file.

    Each entry:
      parent_class    – name of the enclosing *Api class
      inner_class     – 'InputSerializer' | 'OutputSerializer' | 'QuerySerializer'
      new_name        – generated module-level name
      decorator_lines – list[str] (may be empty)
      class_lines     – list[str] (class def + body, original 4-space indent)
      block_start     – line index of first decorator or class def
      block_end       – first line NOT in block (raw, may be blank separator line)
    """
    lines = filepath.read_text().splitlines(keepends=True)
    results: list[dict] = []
    current_api_class: str | None = None

    for i, line in enumerate(lines):
        s = line.rstrip("\n")

        # Track which top-level *Api class we're in
        m = re.match(r"^class\s+(\w+)\s*[\(:]", s)
        if m:
            name = m.group(1)
            current_api_class = name if name.endswith("Api") else None
            continue

        if current_api_class is None:
            continue

        # Match 4-space-indented inner serializer class inside an Api class
        inner_m = re.match(r"^    class\s+(\w+)\s*\(", s)
        if not inner_m or inner_m.group(1) not in INLINE_SERIALIZER_NAMES:
            continue

        inner_class = inner_m.group(1)
        decorators, deco_start = _find_preceding_decorators(lines, i)
        class_lines, block_end = _extract_class_block(lines, i)

        base = current_api_class[:-3] if current_api_class.endswith("Api") else current_api_class
        new_name = f"{base}{inner_class}"

        results.append({
            "parent_class": current_api_class,
            "inner_class": inner_class,
            "new_name": new_name,
            "decorator_lines": decorators,
            "class_lines": class_lines,
            "block_start": deco_start,
            "block_end": block_end,
        })

    return results


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def _get_serializers_path(api_file: Path) -> Path | None:
    """Map an API file to its corresponding serializers module file."""
    try:
        rel = api_file.relative_to(PROJECT_ROOT)
    except ValueError:
        return None

    parts = list(rel.parts)
    if "apis" not in parts:
        return None

    idx = parts.index("apis")
    prefix = parts[:idx]  # e.g. ['core', 'notifications']
    after = parts[idx + 1 :]  # e.g. ['preferences.py'] or ['content_entry', 'action.py']

    if not after:
        return None

    if len(after) == 1:
        resource_file = after[0]
    else:
        resource_file = after[0] + ".py"

    return PROJECT_ROOT.joinpath(*prefix, "serializers", resource_file)


def _module_import_path(ser_file: Path) -> str:
    """Return dotted Python import path for a .py file."""
    rel = ser_file.relative_to(PROJECT_ROOT)
    parts = list(rel.parts)
    if parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    return ".".join(parts)


# ---------------------------------------------------------------------------
# Code generation helpers
# ---------------------------------------------------------------------------


def _deindent(lines: list[str], n: int = 4) -> list[str]:
    """Remove exactly n leading spaces from each non-blank line."""
    prefix = " " * n
    out: list[str] = []
    for line in lines:
        s = line.rstrip("\n")
        if not s.strip():
            out.append("\n")
        elif s.startswith(prefix):
            out.append(s[n:] + "\n")
        else:
            out.append(line)
    return out


def _build_ser_class_text(info: dict) -> str:
    """Build de-indented, renamed serializer class text for the serializers file."""
    all_lines = info["decorator_lines"] + info["class_lines"]
    deindented = _deindent(all_lines, n=4)

    inner = info["inner_class"]
    new_name = info["new_name"]
    renamed: list[str] = []
    for line in deindented:
        renamed.append(re.sub(r"^(class\s+)" + re.escape(inner) + r"(\s*\()", rf"\g<1>{new_name}\2", line))

    return "\n\n" + "".join(renamed).rstrip("\n") + "\n"


def _uses_symbol(lines: list[str], symbol: str) -> bool:
    return any(symbol in line for line in lines)


def _ensure_import_line(content: str, import_line: str) -> str:
    """Add import_line after existing import block if not already present."""
    if import_line in content:
        return content
    lines = content.splitlines(keepends=True)
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith(("from ", "import ")):
            insert_at = i + 1
    lines.insert(insert_at, import_line + "\n")
    return "".join(lines)


def _cleanup_unused_import(api_text: str, symbol: str) -> str:
    """
    If `symbol` is not used outside import lines, remove it from any import.
    Handles single-line and multi-line (parenthesized) import blocks.
    """
    # Strip all import lines to get just the body
    body = re.sub(r"^(from|import)\s.*$", "", api_text, flags=re.MULTILINE)
    body = re.sub(r"from\s+\S+\s+import\s*\([^)]*\)", "", body, flags=re.DOTALL)

    if re.search(r"\b" + re.escape(symbol) + r"\b", body):
        return api_text  # still in use

    # Remove from multi-line import block (4-space indented entry)
    api_text = re.sub(r"^    " + re.escape(symbol) + r",?\n", "", api_text, flags=re.MULTILINE)
    # Remove ', symbol' or 'symbol, ' from single-line imports
    api_text = re.sub(r",\s*\b" + re.escape(symbol) + r"\b", "", api_text)
    api_text = re.sub(r"\b" + re.escape(symbol) + r"\b\s*,\s*", "", api_text)
    # Remove standalone 'symbol' (only name on single-line import)
    return re.sub(r"^from \S+ import " + re.escape(symbol) + r"\s*\n", "", api_text, flags=re.MULTILINE)


def _insert_import_block_in_api(api_text: str, import_block: str) -> str:
    """Insert import block after the last top-level from/import line in an API file.

    Handles multi-line parenthesized imports correctly by scanning past the closing `)`
    before choosing the insertion point.
    """
    lines = api_text.splitlines(keepends=True)

    last_import_start = -1
    for i, line in enumerate(lines):
        if line.startswith(("from ", "import ")):
            last_import_start = i

    if last_import_start == -1:
        lines.insert(0, import_block + "\n")
        return "".join(lines)

    insert_at = last_import_start + 1
    if "(" in lines[last_import_start]:
        depth = lines[last_import_start].count("(") - lines[last_import_start].count(")")
        j = last_import_start + 1
        while depth > 0 and j < len(lines):
            depth += lines[j].count("(") - lines[j].count(")")
            j += 1
        insert_at = j

    lines.insert(insert_at, import_block + "\n")
    return "".join(lines)


# ---------------------------------------------------------------------------
# __init__.py management
# ---------------------------------------------------------------------------


def _update_init_file(init_file: Path, module_name: str, new_names: list[str], dry_run: bool) -> None:
    """
    Add new_names from .module_name to an __init__.py barrel.

    - If __init__.py does not exist: create it with import block + __all__.
    - If it exists but has no import from .module_name: append import block + __all__ entries.
    - If it exists and already imports from .module_name: extend that import block + __all__.
    """
    import_line = f"from .{module_name} import ("

    if not init_file.exists():
        import_block = import_line + "\n" + "".join(f"    {n},\n" for n in new_names) + ")\n"
        all_block = "\n__all__ = [\n" + "".join(f'    "{n}",\n' for n in new_names) + "]\n"
        content = import_block + all_block
        if dry_run:
            pass
        else:
            init_file.write_text(content)
        return

    content = init_file.read_text()
    original = content

    if import_line in content:
        # Extend existing import block — insert names before the closing )
        idx = content.index(import_line)
        close = content.index(")\n", idx)
        addition = "".join(f"    {n},\n" for n in new_names)
        content = content[:close] + addition + content[close:]
    else:
        # Add a new import block (before __all__ if present, else at end of imports)
        new_block = "\n" + import_line + "\n" + "".join(f"    {n},\n" for n in new_names) + ")\n"
        if "__all__" in content:
            idx = content.index("__all__")
            content = content[:idx] + new_block + "\n" + content[idx:]
        else:
            # After last import line
            lines = content.splitlines(keepends=True)
            insert_at = 0
            for i, line in enumerate(lines):
                if line.startswith(("from ", "import ")):
                    insert_at = i + 1
            lines.insert(insert_at, new_block + "\n")
            content = "".join(lines)

    # Extend __all__ if present
    if "__all__" in content:
        close_bracket = content.rindex("]")
        all_additions = "".join(f'    "{n}",\n' for n in new_names)
        content = content[:close_bracket] + all_additions + content[close_bracket:]

    if content != original:
        if dry_run:
            pass
        else:
            init_file.write_text(content)


# ---------------------------------------------------------------------------
# Main transformation
# ---------------------------------------------------------------------------


def transform_file(api_file: Path, dry_run: bool = True) -> bool:
    """Transform one API file. Returns True if changes exist."""
    infos = parse_api_file(api_file)
    if not infos:
        return False

    ser_file = _get_serializers_path(api_file)
    if ser_file is None:
        return False

    import_module = _module_import_path(ser_file)
    api_file.relative_to(PROJECT_ROOT)
    ser_file.relative_to(PROJECT_ROOT)

    for info in infos:
        pass

    if dry_run:
        init_file = ser_file.parent / "__init__.py"
        module_name = ser_file.stem
        new_names = [info["new_name"] for info in infos]
        _update_init_file(init_file, module_name, new_names, dry_run=True)
        return True

    # -----------------------------------------------------------------------
    # Apply changes
    # -----------------------------------------------------------------------

    api_lines = api_file.read_text().splitlines(keepends=True)
    ser_content = ser_file.read_text() if ser_file.exists() else "from rest_framework import serializers\n"

    # Ensure necessary imports in serializers file
    all_class_lines = [line for info in infos for line in info["class_lines"]]
    all_deco_lines = [line for info in infos for line in info["decorator_lines"]]
    if _uses_symbol(all_class_lines, "serializers."):
        ser_content = _ensure_import_line(ser_content, "from rest_framework import serializers")
    if _uses_symbol(all_class_lines, "inline_serializer"):
        ser_content = _ensure_import_line(ser_content, "from core.api.utils import inline_serializer")
    if _uses_symbol(all_deco_lines, "extend_schema_serializer"):
        ser_content = _ensure_import_line(ser_content, "from drf_spectacular.utils import extend_schema_serializer")
    if _uses_symbol(all_class_lines, "RevisionSerializer"):
        ser_content = _ensure_import_line(ser_content, "from core.api.serializers import RevisionSerializer")

    # Build serializer class additions (forward order for readability)
    ser_additions = ""
    for info in infos:
        ser_additions += _build_ser_class_text(info)

    ser_content = ser_content.rstrip("\n") + "\n" + ser_additions

    # Apply replacements to API file (reverse order to preserve indices)
    new_names: list[str] = []
    for info in sorted(infos, key=lambda x: x["block_start"], reverse=True):
        replacement = f"    {info['inner_class']} = {info['new_name']}\n"
        api_lines[info["block_start"] : info["block_end"]] = [replacement]
        new_names.insert(0, info["new_name"])

    api_text = "".join(api_lines)

    # Add import from serializers module
    import_block = f"from {import_module} import (\n" + "".join(f"    {n},\n" for n in new_names) + ")\n"
    api_text = _insert_import_block_in_api(api_text, import_block)

    # Remove imports that are no longer used after inline classes are moved out
    api_text = _cleanup_unused_import(api_text, "extend_schema_serializer")
    api_text = _cleanup_unused_import(api_text, "RevisionSerializer")
    api_text = _cleanup_unused_import(api_text, "serializers")

    # Write API file and serializers file
    ser_file.parent.mkdir(parents=True, exist_ok=True)
    api_file.write_text(api_text)
    ser_file.write_text(ser_content)

    # Update __init__.py
    init_file = ser_file.parent / "__init__.py"
    _update_init_file(init_file, ser_file.stem, new_names, dry_run=False)

    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Move inline Input/Output/QuerySerializer classes from API bodies to serializer modules."
    )
    parser.add_argument("path", type=Path, help="API .py file or directory")
    parser.add_argument("--dry-run", action="store_true", help="Print changes, write nothing")
    parser.add_argument(
        "--skip-history",
        action="store_true",
        default=False,
        help="Skip history.py and audit.py files.",
    )
    args = parser.parse_args()

    target: Path = args.path
    if not target.is_absolute():
        target = Path.cwd() / target

    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(f for f in target.rglob("*.py") if "__pycache__" not in str(f))
    else:
        sys.exit(1)

    if args.skip_history:
        files = [f for f in files if f.name not in ("history.py", "audit.py")]

    changed = 0
    for f in files:
        if transform_file(f, dry_run=args.dry_run):
            changed += 1


if __name__ == "__main__":
    main()
