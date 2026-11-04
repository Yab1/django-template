from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from core.common.services.model_update import model_update


@dataclass(frozen=True)
class NestedSpec:
    """Describe a nested child payload for scaffolded create/update helpers."""

    key: str
    model: type[models.Model]
    parent_field: str
    many: bool = False
    related_accessor: str | None = None
    m2m_fields: tuple[str, ...] = ()
    nested: tuple[NestedSpec, ...] = field(default_factory=tuple)


def m2m_set_if_given(instance: models.Model, field_name: str, value: Any) -> None:
    """Call ``.set(value)`` on an M2M when ``value`` is not ``None``."""
    if value is None:
        return
    getattr(instance, field_name).set(value)


def _split_child_payload(
    data: dict[str, Any],
    *,
    m2m_fields: tuple[str, ...],
    nested: tuple[NestedSpec, ...],
    parent_field: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    nested_keys = {spec.key for spec in nested}
    m2m_names = set(m2m_fields)
    scalars: dict[str, Any] = {}
    nested_payloads: dict[str, Any] = {}
    m2ms: dict[str, Any] = {}

    for key, value in data.items():
        if key in nested_keys:
            nested_payloads[key] = value
        elif key in m2m_names:
            m2ms[key] = value
        elif key in {parent_field, f"{parent_field}_id"}:
            continue
        else:
            scalars[key] = value

    return scalars, nested_payloads, m2ms


def _apply_nested(
    *,
    parent: models.Model,
    nested_payloads: dict[str, Any],
    nested: tuple[NestedSpec, ...],
) -> None:
    for spec in nested:
        payload = nested_payloads.get(spec.key)
        if payload is None:
            continue
        if spec.many:
            children_create(
                model=spec.model,
                parent_field=spec.parent_field,
                parent=parent,
                items=payload,
                m2m_fields=spec.m2m_fields,
                nested=spec.nested,
            )
        else:
            one_to_one_upsert(
                related_accessor=spec.related_accessor or spec.key,
                model=spec.model,
                parent_field=spec.parent_field,
                parent=parent,
                data=payload,
                m2m_fields=spec.m2m_fields,
                nested=spec.nested,
            )


def _create_child(
    *,
    model: type[models.Model],
    parent_field: str,
    parent: models.Model,
    data: dict[str, Any],
    m2m_fields: tuple[str, ...] = (),
    nested: tuple[NestedSpec, ...] = (),
) -> models.Model:
    scalars, nested_payloads, m2ms = _split_child_payload(
        data,
        m2m_fields=m2m_fields,
        nested=nested,
        parent_field=parent_field,
    )
    instance = model(**{parent_field: parent, **scalars})
    instance.full_clean()
    instance.save()

    for name, value in m2ms.items():
        getattr(instance, name).set(value)

    _apply_nested(parent=instance, nested_payloads=nested_payloads, nested=nested)
    return instance


def children_create(
    *,
    model: type[models.Model],
    parent_field: str,
    parent: models.Model,
    items: list[dict[str, Any]] | None,
    m2m_fields: tuple[str, ...] = (),
    nested: tuple[NestedSpec, ...] = (),
) -> list[models.Model]:
    """Create reverse-FK children from a list of payload dicts."""
    if not items:
        return []

    created: list[models.Model] = []
    for item in items:
        created.append(
            _create_child(
                model=model,
                parent_field=parent_field,
                parent=parent,
                data=item,
                m2m_fields=m2m_fields,
                nested=nested,
            )
        )
    return created


def children_replace(
    *,
    manager: models.Manager,
    model: type[models.Model],
    parent_field: str,
    parent: models.Model,
    items: list[dict[str, Any]] | None,
    m2m_fields: tuple[str, ...] = (),
    nested: tuple[NestedSpec, ...] = (),
) -> list[models.Model]:
    """
    Replace reverse-FK children.

    ``items is None`` means the caller did not send the nested key — leave as-is.
    Otherwise delete existing rows and recreate from ``items``.
    """
    if items is None:
        return list(manager.all())

    manager.all().delete()
    return children_create(
        model=model,
        parent_field=parent_field,
        parent=parent,
        items=items,
        m2m_fields=m2m_fields,
        nested=nested,
    )


def one_to_one_upsert(
    *,
    related_accessor: str,
    model: type[models.Model],
    parent_field: str,
    parent: models.Model,
    data: dict[str, Any] | None,
    m2m_fields: tuple[str, ...] = (),
    nested: tuple[NestedSpec, ...] = (),
) -> models.Model | None:
    """
    Create or update a single related child.

    ``data is None`` means the nested key was omitted — leave as-is.
    """
    if data is None:
        return None

    try:
        existing = getattr(parent, related_accessor)
    except ObjectDoesNotExist:
        existing = None
    except AttributeError:
        existing = None

    if existing is None:
        return _create_child(
            model=model,
            parent_field=parent_field,
            parent=parent,
            data=data,
            m2m_fields=m2m_fields,
            nested=nested,
        )

    scalars, nested_payloads, m2ms = _split_child_payload(
        data,
        m2m_fields=m2m_fields,
        nested=nested,
        parent_field=parent_field,
    )
    fields = list(scalars.keys())
    model_update(instance=existing, fields=fields, data=scalars)

    for name, value in m2ms.items():
        getattr(existing, name).set(value)

    # Nested many: replace when key present; nested one: upsert.
    for spec in nested:
        if spec.key not in nested_payloads:
            continue
        payload = nested_payloads[spec.key]
        if spec.many:
            children_replace(
                manager=getattr(existing, spec.related_accessor or spec.key),
                model=spec.model,
                parent_field=spec.parent_field,
                parent=existing,
                items=payload,
                m2m_fields=spec.m2m_fields,
                nested=spec.nested,
            )
        else:
            one_to_one_upsert(
                related_accessor=spec.related_accessor or spec.key,
                model=spec.model,
                parent_field=spec.parent_field,
                parent=existing,
                data=payload,
                m2m_fields=spec.m2m_fields,
                nested=spec.nested,
            )

    return existing
