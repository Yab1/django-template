#!/usr/bin/env python3
"""Build vaccine-code fixtures from FHIR R4 expansion (single CVX CodeSystem)."""

import json
import uuid
from pathlib import Path

CVX_URL = "http://hl7.org/fhir/sid/cvx"
VALUESET_URL = "http://hl7.org/fhir/ValueSet/vaccine-code"
FHIR_VERSION = "4.0.1"
FIXTURE_TS = "2026-06-10T15:00:00Z"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "core/terminology/fixtures/vaccine_code"


def load_concepts(tsv_path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in tsv_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            raise ValueError(f"Expected 3 tab columns, got {len(parts)}: {line!r}")
        code, system, display = parts
        system = system.strip()
        if system != CVX_URL:
            raise ValueError(f"Expected system {CVX_URL!r}, got {system!r} for code {code!r}")
        rows.append((code.strip(), display.strip()))
    return rows


def build_code_system_fixture(
    *,
    cs_pk: str,
    concept_rows: list[tuple[str, str, str]],
    ts: str,
) -> list[dict]:
    rows: list[dict] = [
        {
            "model": "terminology.codesystem",
            "pk": cs_pk,
            "fields": {
                "url": CVX_URL,
                "name": "CVX",
                "title": "CVX Vaccine Codes",
                "version": FHIR_VERSION,
                "status": None,
                "description": "CDC Vaccine Codes (CVX).",
                "is_visible": True,
                "deleted_at": None,
                "deleted_by": None,
                "created_at": ts,
                "updated_at": ts,
                "metadata": {},
            },
        }
    ]
    for concept_pk, code, display in concept_rows:
        rows.append({
            "model": "terminology.concept",
            "pk": concept_pk,
            "fields": {
                "code_system": cs_pk,
                "parent": None,
                "code": code,
                "display": display,
                "definition": "",
                "active": True,
                "created_at": ts,
                "updated_at": ts,
                "metadata": {},
            },
        })
    return rows


def build_value_set_fixture(
    *,
    member_rows: list[tuple[str, str]],
    ts: str,
) -> list[dict]:
    vs_pk = str(uuid.uuid4())
    rows: list[dict] = [
        {
            "model": "terminology.valueset",
            "pk": vs_pk,
            "fields": {
                "url": VALUESET_URL,
                "name": "vaccine-code",
                "title": "Vaccine Administered Value Set",
                "version": FHIR_VERSION,
                "status": None,
                "experimental": False,
                "date": None,
                "publisher": "",
                "description": "This identifies the vaccine substance administered - CVX codes.",
                "immutable": True,
                "created_at": ts,
                "updated_at": ts,
                "metadata": {},
            },
        }
    ]
    for concept_pk, display in member_rows:
        rows.append({
            "model": "terminology.valuesetmember",
            "pk": str(uuid.uuid4()),
            "fields": {
                "value_set": vs_pk,
                "concept": concept_pk,
                "display": display,
                "inactive": None,
                "abstract": None,
                "created_at": ts,
                "updated_at": ts,
                "metadata": {},
            },
        })
    return rows


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    tsv_path = repo_root / "temp/vaccine_code_expansion.tsv"
    concepts = load_concepts(tsv_path)

    codes = [code for code, _display in concepts]
    if len(codes) != len(set(codes)):
        raise SystemExit("Duplicate concept codes in expansion TSV")

    cs_pk = str(uuid.uuid4())
    concept_rows: list[tuple[str, str, str]] = []
    member_rows: list[tuple[str, str]] = []
    for code, display in concepts:
        concept_pk = str(uuid.uuid4())
        concept_rows.append((concept_pk, code, display))
        member_rows.append((concept_pk, display))

    code_system_payload = build_code_system_fixture(cs_pk=cs_pk, concept_rows=concept_rows, ts=FIXTURE_TS)
    value_set_payload = build_value_set_fixture(member_rows=member_rows, ts=FIXTURE_TS)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cs_path = OUTPUT_DIR / "code_system.json"
    vs_path = OUTPUT_DIR / "value_set.json"
    cs_path.write_text(json.dumps(code_system_payload, indent=2) + "\n", encoding="utf-8")
    vs_path.write_text(json.dumps(value_set_payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
