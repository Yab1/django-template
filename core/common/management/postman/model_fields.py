"""Resolve Django models and terminology.Concept FK fields for Postman generation."""

import importlib
from functools import lru_cache

from django.apps import apps
from django.db import models
from django.db.models.fields.related import ForeignKey, ManyToManyField

CONCEPT_MODEL_LABEL = "terminology.concept"

# Path/query params that are never Concept FKs.
_NON_CONCEPT_ID_SUFFIXES = ("_history_id",)
_NON_CONCEPT_ID_EXACT = frozenset({"id", "pk"})


def _resource_folder_to_class_name(resource_folder: str) -> str:
    return "".join(part.capitalize() for part in resource_folder.split("_"))


def resolve_model_for_resource(app_label: str, resource_folder: str) -> type[models.Model] | None:
    """Best-effort model class for a scaffolded resource (e.g. accession -> Accession)."""
    class_name = _resource_folder_to_class_name(resource_folder)
    try:
        return apps.get_model(app_label, class_name)
    except LookupError:
        pass

    try:
        package = importlib.import_module(f"core.{app_label}.models")
    except ImportError:
        return None

    if hasattr(package, class_name):
        candidate = getattr(package, class_name)
        if isinstance(candidate, type) and issubclass(candidate, models.Model):
            return candidate

    try:
        submodule = importlib.import_module(f"core.{app_label}.models.{resource_folder}")
        candidate = getattr(submodule, class_name, None)
        if isinstance(candidate, type) and issubclass(candidate, models.Model):
            return candidate
    except ImportError:
        pass

    return None


def _related_is_terminology_concept(field: models.Field) -> bool:
    if isinstance(field, ForeignKey):
        remote = field.remote_field.model
        return remote._meta.label_lower == CONCEPT_MODEL_LABEL
    if isinstance(field, ManyToManyField):
        remote = field.remote_field.model
        return remote._meta.label_lower == CONCEPT_MODEL_LABEL
    return False


@lru_cache(maxsize=128)
def concept_id_field_names_for_model(model: type[models.Model]) -> frozenset[str]:
    """
    Serializer-style input names for Concept bindings on ``model``.

    ForeignKey ``status`` -> ``status_id``; ManyToMany ``category`` -> ``category_ids`` when
    the reverse relation uses an explicit through (otherwise keep ``category`` for rare cases).
    """
    names: set[str] = set()
    for field in model._meta.get_fields():
        if not _related_is_terminology_concept(field):
            continue
        if isinstance(field, ForeignKey):
            names.add(f"{field.name}_id")
        elif isinstance(field, ManyToManyField):
            names.add(f"{field.name}_ids")
            names.add(field.name)
    return frozenset(names)


def is_terminology_concept_id_field(
    field_name: str,
    *,
    model: type[models.Model] | None,
) -> bool:
    """True when ``field_name`` is a Concept FK (or M2M) on ``model``."""
    if field_name in _NON_CONCEPT_ID_EXACT:
        return False
    if not field_name.endswith("_id") and not field_name.endswith("_ids"):
        return False
    if any(field_name.endswith(suffix) for suffix in _NON_CONCEPT_ID_SUFFIXES):
        return False
    if model is None:
        return False
    allowed = concept_id_field_names_for_model(model)
    if field_name in allowed:
        return True
    # Allow ``status_id`` when model has ``status`` Concept FK even if naming differs slightly.
    if field_name.endswith("_id"):
        stem = field_name[: -len("_id")]
        return f"{stem}_id" in allowed
    return False


def filter_terminology_concept_fields(
    field_names: set[str],
    *,
    app_label: str,
    resource_folder: str,
) -> set[str]:
    """Keep only names that map to ``terminology.Concept`` on the resource model."""
    model = resolve_model_for_resource(app_label, resource_folder)
    if model is None:
        return set()
    return {name for name in field_names if is_terminology_concept_id_field(name, model=model)}


def filter_path_param_names(path_param_names: list[str]) -> list[str]:
    """Drop path params that are never Concept FKs (pk, history navigation, etc.)."""
    filtered: list[str] = []
    for name in path_param_names:
        if name in _NON_CONCEPT_ID_EXACT:
            continue
        if any(name.endswith(suffix) for suffix in _NON_CONCEPT_ID_SUFFIXES):
            continue
        filtered.append(name)
    return filtered
