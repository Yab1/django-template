"""
Map terminology constants and fixtures to Concept PKs for Postman collections.

Follows ``.cursor/rules/postman-terminology-fixtures.mdc``:
- ``*_CODESYSTEM_URL`` in ``core/<app>/constants.py`` and ``core/common/constants/terminology_urls.py``
- ``Concept.pk`` from ``core/terminology/fixtures/<bundle>/code_system.json`` (and app fixtures)
- Request bodies use direct Concept.pk UUID values; no collection variables for terminology fields.
"""

import ast
import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from django.conf import settings

_CODESYSTEM_URL_SUFFIX = "_CODESYSTEM_URL"
_FIELD_ID_SUFFIX = "_id"

# Stable sample codes (first match per CodeSystem wins).
PREFERRED_CONCEPT_CODES: tuple[str, ...] = (
    "planned",
    "draft",
    "active",
    "registered",
    "preliminary",
    "final",
    "booked",
    "arrived",
    "finished",
    "amb",
    "home",
    "inpatient",
    "outpatient",
    "billable",
    "completed",
    "routine",
)


@dataclass(frozen=True)
class ConstantUrl:
    app: str
    name: str
    url: str
    file_path: str


@dataclass(frozen=True)
class ConceptFixture:
    pk: str
    code: str
    fixture_path: str


@dataclass(frozen=True)
class TerminologyBinding:
    field_name: str
    constant_name: str
    codesystem_url: str
    concept: ConceptFixture


def _core_dir() -> Path:
    return Path(settings.BASE_DIR) / "core"


def _discover_constant_files() -> list[Path]:
    core_dir = _core_dir()
    files = sorted(core_dir.rglob("constants.py"))
    terminology_urls = core_dir / "common" / "constants" / "terminology_urls.py"
    if terminology_urls.is_file() and terminology_urls not in files:
        files.append(terminology_urls)
    return files


def _app_name_for_path(path: Path) -> str:
    try:
        rel = path.relative_to(_core_dir())
    except ValueError:
        return "unknown"
    return rel.parts[0] if rel.parts else "common"


def _extract_constant_urls(path: Path) -> list[ConstantUrl]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return []

    app = _app_name_for_path(path)
    items: list[ConstantUrl] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        name = target.id
        if not name.endswith(_CODESYSTEM_URL_SUFFIX):
            continue
        value = node.value
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            continue
        url = value.value.strip()
        if not url.startswith(("http://", "https://")):
            continue
        items.append(ConstantUrl(app=app, name=name, url=url, file_path=str(path)))
    return items


def _discover_fixture_files() -> list[Path]:
    core_dir = _core_dir()
    return sorted(p for p in core_dir.rglob("fixtures/**/*.json") if p.is_file())


@lru_cache(maxsize=1)
def _load_constants_index() -> dict[str, ConstantUrl]:
    index: dict[str, ConstantUrl] = {}
    for path in _discover_constant_files():
        for item in _extract_constant_urls(path):
            index[item.name] = item
    return index


@lru_cache(maxsize=1)
def _load_codesystem_concepts() -> dict[str, list[ConceptFixture]]:
    """CodeSystem URL -> concepts (fixture order preserved)."""
    mapping: dict[str, list[ConceptFixture]] = {}
    for fixture_path in _discover_fixture_files():
        try:
            rows = json.loads(fixture_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(rows, list):
            continue

        codesystem_pk = None
        codesystem_url = None
        for row in rows:
            if row.get("model") == "terminology.codesystem":
                codesystem_pk = row.get("pk")
                codesystem_url = row.get("fields", {}).get("url")
                break
        if not codesystem_url:
            continue

        rel_path = str(fixture_path.relative_to(settings.BASE_DIR))
        for row in rows:
            if row.get("model") != "terminology.concept":
                continue
            fields = row.get("fields", {})
            if codesystem_pk and fields.get("code_system") != codesystem_pk:
                continue
            mapping.setdefault(codesystem_url, []).append(
                ConceptFixture(pk=row["pk"], code=fields.get("code", ""), fixture_path=rel_path),
            )
    return mapping


def _pick_preferred_concept(concepts: list[ConceptFixture]) -> ConceptFixture | None:
    if not concepts:
        return None
    by_code = {concept.code: concept for concept in concepts}
    for code in PREFERRED_CONCEPT_CODES:
        if code in by_code:
            return by_code[code]
    return concepts[0]


def _resource_prefix_upper(resource_folder: str) -> str:
    return resource_folder.upper()


def _constant_candidates_for_field(field_name: str, resource_folder: str) -> list[str]:
    if not field_name.endswith(_FIELD_ID_SUFFIX):
        return []
    stem = field_name[: -len(_FIELD_ID_SUFFIX)]
    resource_upper = _resource_prefix_upper(resource_folder)
    candidates = [
        f"{resource_upper}_{stem.upper()}_CODESYSTEM_URL",
        f"{stem.upper()}_CODESYSTEM_URL",
    ]
    resource_snake = resource_folder
    if stem.startswith(f"{resource_snake}_"):
        trimmed = stem[len(resource_snake) + 1 :]
        if trimmed:
            candidates.append(f"{resource_upper}_{trimmed.upper()}_CODESYSTEM_URL")
            candidates.append(f"{trimmed.upper()}_CODESYSTEM_URL")
    return candidates


def _field_candidates_for_constant(constant_name: str, resource_folder: str) -> list[str]:
    if not constant_name.endswith(_CODESYSTEM_URL_SUFFIX):
        return []
    stem = constant_name[: -len(_CODESYSTEM_URL_SUFFIX)].lower()
    resource = resource_folder.lower()
    candidates = [f"{stem}_id"]
    resource_parts = resource.split("_")
    stem_parts = stem.split("_")
    if len(stem_parts) > len(resource_parts) and stem_parts[: len(resource_parts)] == resource_parts:
        trimmed = "_".join(stem_parts[len(resource_parts) :])
        if trimmed:
            candidates.append(f"{trimmed}_id")
    if stem.endswith(f"_{resource}") or stem == resource:
        pass
    last = stem_parts[-1] if stem_parts else stem
    if last:
        candidates.append(f"{last}_id")
    # Deduplicate preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for name in candidates:
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


class TerminologyResolver:
    """Resolve Concept ``*_id`` serializer fields to fixture UUIDs via URL constants."""

    def __init__(
        self,
        *,
        app_label: str,
        constants: dict[str, ConstantUrl] | None = None,
        concepts_by_url: dict[str, list[ConceptFixture]] | None = None,
    ) -> None:
        self.app_label = app_label
        self._constants = constants if constants is not None else _load_constants_index()
        self._concepts_by_url = concepts_by_url if concepts_by_url is not None else _load_codesystem_concepts()
        self._app_constants = {name: item for name, item in self._constants.items() if item.app == app_label}

    @classmethod
    def for_app(cls, app_label: str) -> "TerminologyResolver":
        return cls(app_label=app_label)

    def resolve_constant_for_field(self, field_name: str, *, resource_folder: str) -> ConstantUrl | None:
        for const_name in _constant_candidates_for_field(field_name, resource_folder):
            if const_name in self._constants:
                return self._constants[const_name]
        stem = field_name[: -len(_FIELD_ID_SUFFIX)] if field_name.endswith(_FIELD_ID_SUFFIX) else field_name
        stem_upper = stem.upper()
        for const_name, item in self._app_constants.items():
            if const_name.endswith(_CODESYSTEM_URL_SUFFIX) and stem_upper in const_name:
                return item
        for const_name, item in self._constants.items():
            if not const_name.endswith(_CODESYSTEM_URL_SUFFIX):
                continue
            if const_name.replace("_CODESYSTEM_URL", "").endswith(stem_upper) or stem_upper in const_name:
                return item
        return None

    def bind_field(self, field_name: str, *, resource_folder: str) -> TerminologyBinding | None:
        constant = self.resolve_constant_for_field(field_name, resource_folder=resource_folder)
        if constant is None:
            return None
        concepts = self._concepts_by_url.get(constant.url, [])
        concept = _pick_preferred_concept(concepts)
        if concept is None:
            return None
        return TerminologyBinding(
            field_name=field_name,
            constant_name=constant.name,
            codesystem_url=constant.url,
            concept=concept,
        )

    def bind_fields(
        self,
        field_names: set[str],
        *,
        resource_folder: str,
    ) -> dict[str, TerminologyBinding]:
        bindings: dict[str, TerminologyBinding] = {}
        for field_name in sorted(field_names):
            if not field_name.endswith(_FIELD_ID_SUFFIX):
                continue
            binding = self.bind_field(field_name, resource_folder=resource_folder)
            if binding is not None:
                bindings[field_name] = binding
        return bindings

    def collection_defaults(
        self,
        field_names: set[str],
        *,
        resource_folder: str,
    ) -> dict[str, dict[str, str]]:
        defaults: dict[str, dict[str, str]] = {}
        for field_name, binding in self.bind_fields(field_names, resource_folder=resource_folder).items():
            defaults[field_name] = {
                "value": binding.concept.pk,
                "description": (
                    f"Concept `{binding.concept.code}` from `{binding.concept.fixture_path}` "
                    f"(constant `{binding.constant_name}`)."
                ),
            }
        return defaults

    def body_var_refs(self, field_names: set[str], *, resource_folder: str) -> dict[str, str]:
        """Direct Concept.pk values for request JSON bodies (no collection variable references)."""
        return self.response_fixture_values(field_names, resource_folder=resource_folder)

    def response_fixture_values(self, field_names: set[str], *, resource_folder: str) -> dict[str, str]:
        """Concrete Concept.pk values for saved response examples."""
        return {
            field_name: binding.concept.pk
            for field_name, binding in self.bind_fields(field_names, resource_folder=resource_folder).items()
        }

    def unbound_concept_id_fields(
        self,
        field_names: set[str],
        *,
        resource_folder: str,
    ) -> list[str]:
        unbound: list[str] = []
        for field_name in sorted(field_names):
            if not field_name.endswith(_FIELD_ID_SUFFIX):
                continue
            if field_name not in self.bind_fields({field_name}, resource_folder=resource_folder):
                unbound.append(field_name)
        return unbound


def resolve_terminology_defaults(
    *,
    app_label: str,
    resource_folder: str,
    field_names: set[str],
) -> dict[str, dict[str, str]]:
    return TerminologyResolver.for_app(app_label).collection_defaults(
        field_names,
        resource_folder=resource_folder,
    )


def terminology_values_for_fields(
    *,
    app_label: str,
    resource_folder: str,
    field_names: set[str],
) -> dict[str, str]:
    """Fixture UUIDs for saved responses and request bodies (direct values, no ``{{variable}}`` refs)."""
    return TerminologyResolver.for_app(app_label).response_fixture_values(
        field_names,
        resource_folder=resource_folder,
    )


def terminology_body_var_refs(
    *,
    app_label: str,
    resource_folder: str,
    field_names: set[str],
) -> dict[str, str]:
    """Direct Concept.pk values for request JSON bodies (no ``{{variable}}`` references)."""
    return TerminologyResolver.for_app(app_label).body_var_refs(
        field_names,
        resource_folder=resource_folder,
    )
