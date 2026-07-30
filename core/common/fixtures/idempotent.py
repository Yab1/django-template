"""Helpers for idempotent fixture loading (replace conflicting rows before loaddata)."""

import json
import os
import uuid
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

from django.apps import apps
from django.core import serializers
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.db.models.deletion import ProtectedError

PK_LOOKUP_CHUNK = 2000
ORPHAN_LOOKUP_CHUNK = 400
# Skip expensive orphan scans on large re-runs when every fixture PK is already loaded.
ORPHAN_SCAN_SKIP_MIN_ENTRIES = 500


def normalize_pk(pk: Any) -> Any:
    """Normalize fixture PK for set lookups (UUID models and integer PK models)."""
    if isinstance(pk, uuid.UUID):
        return pk
    if isinstance(pk, int):
        return pk
    text = str(pk)
    try:
        return uuid.UUID(text)
    except ValueError:
        if text.lstrip("-").isdigit():
            return int(text)
        raise


def load_fixture_entries(fixture_path: str | os.PathLike) -> list[dict[str, Any]]:
    path = Path(fixture_path)
    with path.open(encoding="utf-8") as fp:
        data = json.load(fp)
    if not isinstance(data, list):
        raise ValueError(f"Expected JSON array in fixture: {path}")
    return data


def unique_field_sets(model: type[models.Model]) -> list[tuple[str, ...]]:
    sets: list[tuple[str, ...]] = []
    seen: set[tuple[str, ...]] = set()

    for constraint in model._meta.constraints:
        if isinstance(constraint, UniqueConstraint) and constraint.condition is None:
            key = tuple(constraint.fields)
            if key not in seen:
                seen.add(key)
                sets.append(key)

    for group in model._meta.unique_together:
        key = tuple(group)
        if key not in seen:
            seen.add(key)
            sets.append(key)

    for field in model._meta.local_concrete_fields:
        if field.unique and not field.primary_key:
            key = (field.name,)
            if key not in seen:
                seen.add(key)
                sets.append(key)

    return sets


def resolve_fixture_field_value(field: models.Field, value: Any) -> Any | None:
    """Map fixture JSON values to DB lookup values (mirrors common loaddata shapes)."""
    if value is None:
        return None
    if isinstance(value, dict):
        return None
    if isinstance(value, list):
        if len(value) == 0:
            return None
        remote_model = getattr(getattr(field, "remote_field", None), "model", None)
        if remote_model == "contenttypes.contenttype" and len(value) == 2:
            from django.contrib.contenttypes.models import ContentType

            app_label, model_name = value[0], value[1]
            return ContentType.objects.get(app_label=app_label, model=model_name).pk
        return None
    return value


def field_filter_kwargs(
    model: type[models.Model],
    field_names: tuple[str, ...],
    fields: dict[str, Any],
) -> dict[str, Any] | None:
    filt: dict[str, Any] = {}
    for name in field_names:
        if name not in fields:
            return None
        try:
            field = model._meta.get_field(name)
        except models.FieldDoesNotExist:
            return None

        if getattr(field, "many_to_many", False):
            return None

        resolved = resolve_fixture_field_value(field, fields[name])
        if resolved is None:
            return None
        filt[name] = resolved
    return filt


def existing_primary_keys(
    model: type[models.Model],
    pks: set,
    *,
    using: str,
) -> set:
    if not pks:
        return set()

    manager = model._base_manager.using(using)
    pk_list = list(pks)
    found: set = set()
    for offset in range(0, len(pk_list), PK_LOOKUP_CHUNK):
        chunk = pk_list[offset : offset + PK_LOOKUP_CHUNK]
        found.update(manager.filter(pk__in=chunk).values_list("pk", flat=True))
    return found


def hard_delete_queryset(qs: models.QuerySet, *, using: str) -> int:
    count = 0
    for obj in qs.iterator():
        try:
            if hasattr(obj, "hard_delete"):
                obj.hard_delete(using=using)
            else:
                obj.delete(using=using)
            count += 1
        except ProtectedError:
            continue
    return count


def collect_entries_from_files(fixture_files: list[str]) -> dict[str, list[dict[str, Any]]]:
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in fixture_files:
        for entry in load_fixture_entries(path):
            model_label = entry.get("model")
            if not model_label:
                continue
            by_model[model_label].append(entry)
    return dict(by_model)


def _entries_by_pk(entries: list[dict[str, Any]]) -> dict[Any, dict[str, Any]]:
    by_pk: dict[Any, dict[str, Any]] = {}
    for entry in entries:
        raw_pk = entry.get("pk")
        if raw_pk is None:
            continue
        by_pk[normalize_pk(raw_pk)] = entry
    return by_pk


def sync_many_to_many_from_fixture_fields(
    *,
    instance: models.Model,
    fields: dict[str, Any],
    using: str,
) -> int:
    """
    Apply M2M lists from fixture JSON onto an existing row.

    Only fields present in ``fields`` with list values are synced (``.set()``).
    Scalar columns on existing PKs are still not updated — use replace/delete or
    a data migration for those.
    """
    synced = 0
    for name, raw_value in fields.items():
        try:
            field = instance._meta.get_field(name)
        except models.FieldDoesNotExist:
            continue
        if not getattr(field, "many_to_many", False):
            continue
        if not isinstance(raw_value, list):
            continue
        # Fixture M2M values may be int or UUID PKs; pass through for Django ``.set()``.
        getattr(instance, name).set(list(raw_value))
        synced += 1
    return synced


def _fixture_metadata(entry: dict[str, Any]) -> dict[str, Any]:
    metadata = (entry.get("fields") or {}).get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def collect_fixture_sets(entries_by_model: dict[str, list[dict[str, Any]]]) -> set[str]:
    fixture_sets: set[str] = set()
    for entries in entries_by_model.values():
        for entry in entries:
            fixture_set = _fixture_metadata(entry).get("fixture_set")
            if fixture_set:
                fixture_sets.add(str(fixture_set))
    return fixture_sets


def collect_fixture_slug_names(
    entries_by_model: dict[str, list[dict[str, Any]]],
    *,
    model_label: str,
    field_name: str,
) -> set[str]:
    names: set[str] = set()
    for entry in entries_by_model.get(model_label, []):
        value = (entry.get("fields") or {}).get(field_name)
        if value:
            names.add(str(value))
    return names


def purge_fixture_set_rows(
    *,
    entries_by_model: dict[str, list[dict[str, Any]]],
    using: str,
    verbosity: int = 1,
    log: Callable[[str], None] | None = None,
) -> int:
    """
    Remove prior rows for the same fixture_set / plan / activity names.

    Needed when fixture PKs change (e.g. regenerated UUIDs) but business keys
    and metadata.fixture_set stay the same. Deletes plan subgraph before
    activity definitions (actions PROTECT activity rows).
    """
    from django.db import connections

    def _noop(_msg: str) -> None:
        return None

    if log is None:
        log = _noop

    fixture_sets = collect_fixture_sets(entries_by_model)
    plan_names = collect_fixture_slug_names(
        entries_by_model,
        model_label="workflows.plandefinition",
        field_name="name",
    )
    activity_names = collect_fixture_slug_names(
        entries_by_model,
        model_label="workflows.activitydefinition",
        field_name="name",
    )
    if not fixture_sets and not plan_names and not activity_names:
        return 0

    connection = connections[using]
    deleted_total = 0

    try:
        plan_model = apps.get_model("workflows.plandefinition")
        activity_model = apps.get_model("workflows.activitydefinition")
        binding_model = apps.get_model("workflows.workflowplanbinding")
    except LookupError:
        return 0

    plan_manager = plan_model._base_manager.using(using)
    plan_query = Q()
    if fixture_sets:
        plan_query |= Q(metadata__fixture_set__in=list(fixture_sets))
    if plan_names:
        plan_query |= Q(name__in=list(plan_names))
    plan_ids = list(plan_manager.filter(plan_query).values_list("pk", flat=True))

    with connection.constraint_checks_disabled():
        if plan_ids:
            child_models = [
                "workflows.plandefinitionactionemission",
                "workflows.plandefinitionactiontrigger",
                "workflows.plandefinitioncondition",
                "workflows.plandefinitionaction",
            ]
            for model_label in child_models:
                try:
                    child_model = apps.get_model(model_label)
                except LookupError:
                    continue
                child_manager = child_model._base_manager.using(using)
                if model_label == "workflows.plandefinitionaction":
                    child_qs = child_manager.filter(plan_definition_id__in=plan_ids)
                else:
                    child_qs = child_manager.filter(plan_definition_action__plan_definition_id__in=plan_ids)
                deleted_total += hard_delete_queryset(child_qs, using=using)

            binding_qs = binding_model._base_manager.using(using).filter(plan_definition_id__in=plan_ids)
            deleted_total += hard_delete_queryset(binding_qs, using=using)

            deleted_total += hard_delete_queryset(plan_manager.filter(pk__in=plan_ids), using=using)

        activity_query = Q()
        if fixture_sets:
            activity_query |= Q(metadata__fixture_set__in=list(fixture_sets))
        if activity_names:
            activity_query |= Q(name__in=list(activity_names))
        if activity_query:
            activity_qs = activity_model._base_manager.using(using).filter(activity_query)
            deleted_total += hard_delete_queryset(activity_qs, using=using)

    if verbosity >= 1 and deleted_total:
        sets_label = ", ".join(sorted(fixture_sets)) if fixture_sets else "(by name)"
        log(f"Purged {deleted_total} prior row(s) for fixture_set {sets_label}")

    return deleted_total


def replace_fixture_rows(
    *,
    entries_by_model: dict[str, list[dict[str, Any]]],
    using: str,
    verbosity: int = 1,
    log: Callable[[str], None] | None = None,
) -> int:
    """
    Delete existing rows that would conflict with fixture entries.

    Removes stale rows that collide on unique constraints (different PK, same
    business key). Rows blocked by PROTECT FKs are left in place;
    ``load_fixture_files`` skips INSERT when the PK already exists.
    """
    from django.db import connections

    def _noop(_msg: str) -> None:
        return None

    if log is None:
        log = _noop

    connection = connections[using]
    deleted_total = purge_fixture_set_rows(
        entries_by_model=entries_by_model,
        using=using,
        verbosity=verbosity,
        log=log,
    )
    model_count = len(entries_by_model)

    with connection.constraint_checks_disabled():
        for model_index, (model_label, entries) in enumerate(entries_by_model.items(), start=1):
            try:
                model = apps.get_model(model_label)
            except LookupError:
                if verbosity >= 2:
                    log(f"skip unknown model label: {model_label}")
                continue

            if verbosity >= 1 and model_count > 3:
                log(f"  replace orphans {model_index}/{model_count}: {model_label} ({len(entries)} row(s))")

            manager = model._base_manager.using(using)
            model_deleted = 0
            fixture_pks = {normalize_pk(entry["pk"]) for entry in entries if entry.get("pk") is not None}

            if len(entries) >= ORPHAN_SCAN_SKIP_MIN_ENTRIES and fixture_pks:
                existing_pks = existing_primary_keys(model, fixture_pks, using=using)
                if existing_pks == fixture_pks:
                    if verbosity >= 2:
                        log(f"  {model_label}: skip orphan scan ({len(fixture_pks)} PKs already loaded)")
                    continue

            for field_set in unique_field_sets(model):
                filters: list[dict[str, Any]] = []
                for entry in entries:
                    filt = field_filter_kwargs(
                        model,
                        field_set,
                        entry.get("fields") or {},
                    )
                    if filt is not None:
                        filters.append(filt)

                for offset in range(0, len(filters), ORPHAN_LOOKUP_CHUNK):
                    chunk = filters[offset : offset + ORPHAN_LOOKUP_CHUNK]
                    query = Q()
                    for filt in chunk:
                        query |= Q(**filt)
                    if not query:
                        continue
                    orphan_qs = manager.filter(query).exclude(pk__in=fixture_pks)
                    model_deleted += hard_delete_queryset(orphan_qs, using=using)

            deleted_total += model_deleted
            if verbosity >= 2 and model_deleted:
                log(f"  {model_label}: removed {model_deleted} row(s)")

    if verbosity >= 1 and deleted_total:
        log(f"Removed {deleted_total} conflicting fixture row(s) before load")

    return deleted_total


def load_fixture_files(
    *,
    fixture_files: list[str],
    entries_by_model: dict[str, list[dict[str, Any]]],
    using: str,
    ignorenonexistent: bool = False,
    verbosity: int = 1,
    log: Callable[[str], None] | None = None,
) -> tuple[int, int, int]:
    """Install fixture objects whose PKs are not already present; sync M2M on existing PKs."""

    def _noop(_msg: str) -> None:
        return None

    if log is None:
        log = _noop

    installed = 0
    skipped = 0
    objects_m2m_synced = 0
    deferred_fields: list = []
    existing_by_model_label: dict[str, set] = {}
    entries_by_pk_by_model: dict[str, dict[Any, dict[str, Any]]] = {}
    model_by_label: dict[str, type[models.Model]] = {}

    for model_label, entries in entries_by_model.items():
        try:
            model = apps.get_model(model_label)
        except LookupError:
            continue
        model_by_label[model_label] = model
        entries_by_pk_by_model[model_label] = _entries_by_pk(entries)
        fixture_pks = set(entries_by_pk_by_model[model_label])
        existing_by_model_label[model_label] = existing_primary_keys(
            model,
            fixture_pks,
            using=using,
        )

    file_count = len(fixture_files)
    if verbosity >= 1 and file_count > 5:
        log(f"Loading {file_count} fixture file(s)...")

    for file_index, path in enumerate(fixture_files, start=1):
        if verbosity >= 1 and file_count > 20 and file_index % 25 == 0:
            log(
                f"  load progress {file_index}/{file_count} files "
                f"(installed={installed} skipped={skipped} m2m_synced={objects_m2m_synced})",
            )

        with Path(path).open(encoding="utf-8") as fp:
            objects = serializers.deserialize(
                "json",
                fp,
                using=using,
                ignorenonexistent=ignorenonexistent,
                handle_forward_references=True,
            )
            for obj in objects:
                model_label = obj.object._meta.label_lower
                existing_pks = existing_by_model_label.get(model_label, set())
                if obj.object.pk in existing_pks:
                    skipped += 1
                    entry = entries_by_pk_by_model.get(model_label, {}).get(normalize_pk(obj.object.pk))
                    model = model_by_label.get(model_label)
                    if entry is not None and model is not None:
                        instance = model._base_manager.using(using).get(pk=obj.object.pk)
                        if sync_many_to_many_from_fixture_fields(
                            instance=instance,
                            fields=entry.get("fields") or {},
                            using=using,
                        ):
                            objects_m2m_synced += 1
                    continue
                obj.save(using=using)
                installed += 1
                existing_by_model_label.setdefault(model_label, set()).add(obj.object.pk)
                if obj.deferred_fields:
                    deferred_fields.append(obj)

    for obj in deferred_fields:
        obj.save_deferred_fields(using=using)

    if verbosity >= 1:
        if skipped:
            log(f"Skipped {skipped} existing fixture object(s)")
        if objects_m2m_synced:
            log(f"Synced M2M on {objects_m2m_synced} existing fixture object(s)")
        if installed:
            log(f"Installed {installed} fixture object(s) from {file_count} file(s)")

    return installed, skipped, objects_m2m_synced
