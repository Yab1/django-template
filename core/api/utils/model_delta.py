"""Serialize django-simple-history ``ModelDelta`` for API responses."""

from __future__ import annotations

from typing import Any

from simple_history.models import DeletedObject, ModelDelta


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, DeletedObject):
        return {
            "deleted": True,
            "model": f"{value.model._meta.app_label}.{value.model.__name__}",
            "pk": value.pk,
        }
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return str(value)


def model_delta_to_api_dict(*, delta: ModelDelta) -> dict[str, Any]:
    """Map ``ModelDelta`` to the shared ``HistoryDiffResponseSerializer`` shape."""
    return {
        "from_history_id": delta.old_record.history_id,
        "to_history_id": delta.new_record.history_id,
        "changed_fields": list(delta.changed_fields),
        "changes": [
            {
                "field": change.field,
                "old": _jsonable(change.old),
                "new": _jsonable(change.new),
            }
            for change in delta.changes
        ],
    }
