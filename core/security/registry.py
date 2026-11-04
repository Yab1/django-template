from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionSpec:
    """Code-owned catalog entry. Synced into permission rows when security app lands."""

    code: str
    name: str
    description: str = ""


_REGISTRY: dict[str, PermissionSpec] = {}


def register_permission(*, code: str, name: str, description: str = "") -> None:
    cleaned = code.strip()
    if not cleaned:
        raise ValueError("Permission code is required.")
    existing = _REGISTRY.get(cleaned)
    spec = PermissionSpec(code=cleaned, name=name.strip(), description=description.strip())
    if existing is not None and existing != spec:
        raise ValueError(f"Permission {cleaned!r} is already registered with a different definition.")
    _REGISTRY[cleaned] = spec


def get_permission_spec(*, code: str) -> PermissionSpec | None:
    return _REGISTRY.get(code.strip())


def all_permission_specs() -> tuple[PermissionSpec, ...]:
    return tuple(_REGISTRY.values())
