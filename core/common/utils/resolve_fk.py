from typing import Any

from django.db import models

from core.common.utils.get_object import get_object


def resolve_fk(
    update_data: dict[str, Any],
    field_name: str,
    model: type[models.Model],
) -> None:
    """
    In-place: turn ``{field_name}_id`` in ``update_data`` into ``field_name`` object.

    Missing ``{field_name}_id`` → no-op.
    ``None`` id → sets ``field_name`` to ``None``.
    Otherwise loads via ``get_object`` (may be ``None`` if the row is missing).
    """
    id_key = f"{field_name}_id"
    if id_key not in update_data:
        return

    pk = update_data.pop(id_key)
    if pk is None:
        update_data[field_name] = None
        return

    update_data[field_name] = get_object(model, id=pk)
