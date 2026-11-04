from __future__ import annotations

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import models


@dataclass(frozen=True)
class FileTarget:
    """Allowlisted upload slot. ``resource`` + ``field`` map to one model."""

    resource: str
    field: str
    model: type[models.Model]
    replace: bool = False
    types: tuple[str, ...] = ()


_REGISTRY: dict[tuple[str, str], FileTarget] = {}


def register_file_target(target: FileTarget) -> None:
    _REGISTRY[(target.resource.lower(), target.field.lower())] = target


def get_file_target(*, resource: str, field: str) -> FileTarget:
    key = (resource.strip().lower(), field.strip().lower())
    target = _REGISTRY.get(key)
    if target is None:
        raise ValidationError({"resource": "Unknown resource and field pair."})
    return target


def model_for_resource(*, resource: str) -> type[models.Model]:
    needle = resource.strip().lower()
    for (res, _), target in _REGISTRY.items():
        if res == needle:
            return target.model
    raise ValidationError({"resource": "Unknown resource."})


def register_default_targets() -> None:
    from core.files.constants import FIELD_FILE, RESOURCE_USER
    from core.users.models import User

    register_file_target(
        FileTarget(resource=RESOURCE_USER, field=FIELD_FILE, model=User, replace=False),
    )
