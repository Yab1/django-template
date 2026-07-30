#!/usr/bin/env python3
"""Regenerate Codex + Claude instructions from .cursor/rules/*.mdc (does not modify Cursor rules)."""

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURSOR_RULES = ROOT / ".cursor/rules"
CODEX_INSTRUCTIONS = ROOT / ".codex/instructions"
CODEX_SKILLS = ROOT / ".codex/skills"
CLAUDE_INSTRUCTIONS = ROOT / ".claude/instructions"
CLAUDE_RULES = ROOT / ".claude/rules"
CLAUDE_SKILLS = ROOT / ".claude/skills"

REF_RE = re.compile(r"\.cursor/rules/([a-z0-9_-]+)\.mdc", re.IGNORECASE)


def parse_frontmatter(text: str) -> tuple[dict[str, str], list[str], str]:
    if not text.startswith("---\n"):
        return {}, [], text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, [], text
    fm_block = text[4:end]
    body = text[end + 5 :]

    meta: dict[str, str] = {}
    globs: list[str] = []
    lines = fm_block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("globs:"):
            rest = line[len("globs:") :].strip()
            if rest:
                globs.extend(p.strip().strip('"').strip("'") for p in rest.split(",") if p.strip())
            else:
                i += 1
                while i < len(lines) and lines[i].startswith("  -"):
                    item = lines[i].split("-", 1)[1].strip().strip('"').strip("'")
                    if item:
                        globs.append(item)
                    i += 1
                continue
        elif ":" in line and not line.startswith(" "):
            key, val = line.split(":", 1)
            meta[key.strip()] = val.strip()
        i += 1

    return meta, globs, body


def rewrite_refs(body: str, instructions_prefix: str) -> str:
    body = REF_RE.sub(rf"{instructions_prefix}/\1.md", body)
    return body.replace(".cursor/rules/", f"{instructions_prefix}/").replace(".mdc", ".md")


def skill_md(name: str, description: str, body: str) -> str:
    short = description[:80]
    return (
        f"---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        f"metadata:\n"
        f"  short-description: {short}\n"
        f"---\n\n"
        f"{body.rstrip()}\n"
    )


def claude_rule_md(globs: list[str], body: str) -> str:
    if not globs:
        return body.rstrip() + "\n"
    paths_yaml = "\n".join(f'  - "{pattern}"' for pattern in globs)
    return f"---\npaths:\n{paths_yaml}\n---\n\n{body.lstrip().rstrip()}\n"


def prune_stale_children(parent: Path, keep_names: set[str], *, is_dir: bool) -> None:
    if not parent.exists():
        return
    for child in parent.iterdir():
        if child.name in keep_names:
            continue
        if is_dir:
            if child.is_dir():
                shutil.rmtree(child)
        elif child.is_file() and child.suffix == ".md":
            child.unlink()


def sync_codex(entries: list[dict]) -> None:
    CODEX_INSTRUCTIONS.mkdir(parents=True, exist_ok=True)
    CODEX_SKILLS.mkdir(parents=True, exist_ok=True)

    always_apply = [e for e in entries if e["always"] and not e["globs"]]
    on_demand = [e for e in entries if not e["always"] and not e["globs"]]

    agents_lines = [
        "# ehr-backend — Codex project instructions",
        "",
        "Duplicated from `.cursor/rules/` for Codex. Regenerate with:",
        "`python3 scripts/sync_from_cursor_rules.py`",
        "",
        "On-demand rules: `.codex/skills/<name>/SKILL.md`. Copies: `.codex/instructions/`.",
        "",
        "---",
        "",
    ]
    for entry in always_apply:
        agents_lines.extend([f"## {entry['name']}", "", entry["codex_body"].rstrip(), "", "---", ""])

    if on_demand:
        agents_lines.extend([
            "## On-demand instruction skills",
            "",
            "Load when relevant (also in `.codex/instructions/`):",
            "",
        ])
        for entry in on_demand:
            agents_lines.append(
                f"- **{entry['name']}** — {entry['description']} → `.codex/skills/{entry['name']}/SKILL.md`"
            )
        agents_lines.append("")

    (ROOT / "AGENTS.md").write_text("\n".join(agents_lines).rstrip() + "\n", encoding="utf-8")

    for entry in on_demand:
        skill_dir = CODEX_SKILLS / entry["name"]
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            skill_md(entry["name"], entry["description"], entry["codex_body"]),
            encoding="utf-8",
        )

    prune_stale_children(CODEX_INSTRUCTIONS, {f"{e['name']}.md" for e in entries}, is_dir=False)
    prune_stale_children(CODEX_SKILLS, {e["name"] for e in on_demand}, is_dir=True)


def sync_claude(entries: list[dict]) -> None:
    CLAUDE_INSTRUCTIONS.mkdir(parents=True, exist_ok=True)
    CLAUDE_RULES.mkdir(parents=True, exist_ok=True)
    CLAUDE_SKILLS.mkdir(parents=True, exist_ok=True)

    launch_rules = [e for e in entries if e["always"] or e["globs"]]
    on_demand = [e for e in entries if not e["always"] and not e["globs"]]

    for entry in launch_rules:
        rule_globs = [] if entry["always"] else entry["globs"]
        (CLAUDE_RULES / f"{entry['name']}.md").write_text(
            claude_rule_md(rule_globs, entry["claude_body"]),
            encoding="utf-8",
        )

    for entry in on_demand:
        skill_dir = CLAUDE_SKILLS / entry["name"]
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            skill_md(entry["name"], entry["description"], entry["claude_body"]),
            encoding="utf-8",
        )

    claude_lines = [
        "# ehr-backend — Claude Code project instructions",
        "",
        "Canonical source: `.cursor/rules/`. Regenerate with:",
        "`python3 scripts/sync_from_cursor_rules.py`",
        "",
        "Always-apply and path-scoped rules load from `.claude/rules/`.",
        "On-demand skills: `.claude/skills/<name>/SKILL.md`. Full copies: `.claude/instructions/`.",
        "",
    ]
    if on_demand:
        claude_lines.extend([
            "## On-demand skills",
            "",
            "Load when relevant (also in `.claude/instructions/`):",
            "",
        ])
        for entry in on_demand:
            claude_lines.append(
                f"- **{entry['name']}** — {entry['description']} → `.claude/skills/{entry['name']}/SKILL.md`"
            )
        claude_lines.append("")

    (ROOT / ".claude/CLAUDE.md").write_text("\n".join(claude_lines).rstrip() + "\n", encoding="utf-8")

    prune_stale_children(CLAUDE_INSTRUCTIONS, {f"{e['name']}.md" for e in entries}, is_dir=False)
    prune_stale_children(CLAUDE_RULES, {f"{e['name']}.md" for e in launch_rules}, is_dir=False)
    prune_stale_children(CLAUDE_SKILLS, {e["name"] for e in on_demand}, is_dir=True)


def main() -> None:
    entries: list[dict] = []
    CODEX_INSTRUCTIONS.mkdir(parents=True, exist_ok=True)
    CLAUDE_INSTRUCTIONS.mkdir(parents=True, exist_ok=True)

    for src in sorted(CURSOR_RULES.glob("*.mdc")):
        raw = src.read_text(encoding="utf-8")
        meta, globs, body = parse_frontmatter(raw)
        codex_body = rewrite_refs(body, ".codex/instructions").lstrip()
        claude_body = rewrite_refs(body, ".claude/instructions").lstrip()

        (CODEX_INSTRUCTIONS / f"{src.stem}.md").write_text(codex_body, encoding="utf-8")
        (CLAUDE_INSTRUCTIONS / f"{src.stem}.md").write_text(claude_body, encoding="utf-8")

        entries.append({
            "name": src.stem,
            "description": meta.get("description", f"Project rule: {src.stem.replace('-', ' ')}"),
            "always": meta.get("alwaysApply", "false").lower() == "true",
            "globs": globs,
            "codex_body": codex_body,
            "claude_body": claude_body,
        })

    sync_codex(entries)
    sync_claude(entries)


if __name__ == "__main__":
    main()
