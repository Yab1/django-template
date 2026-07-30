"""Reusable serializers for bulk request and response shapes."""

from typing import Any

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from core.api.utils.serializers import create_serializer_class

DEFAULT_BULK_MIN_ITEMS = 1
DEFAULT_BULK_MAX_ITEMS = 100


def build_bulk_input_serializer(
    *,
    component_name: str,
    item_serializer: type[serializers.Serializer],
    min_items: int = DEFAULT_BULK_MIN_ITEMS,
    max_items: int = DEFAULT_BULK_MAX_ITEMS,
    items_field_name: str = "items",
) -> type[serializers.Serializer]:
    """
    Build a serializer for the standard bulk-create request envelope.

    Shape::

        {"items": [<item>, <item>, ...]}

    Validation is enforced by DRF's ``ListSerializer`` (``min_length`` /
    ``max_length`` / ``allow_empty=False``) so individual APIs do not need to
    re-implement length checks in ``validate_<field>``.
    """

    list_kwargs: dict[str, Any] = {
        "many": True,
        "allow_empty": False,
        "min_length": min_items,
        "max_length": max_items,
    }
    serializer_class = create_serializer_class(
        name=component_name,
        fields={items_field_name: item_serializer(**list_kwargs)},
    )
    return extend_schema_serializer(component_name=component_name)(serializer_class)


def build_bulk_output_serializer(
    *,
    component_name: str,
    item_serializer: type[serializers.Serializer],
    items_field_name: str = "items",
) -> type[serializers.Serializer]:
    """
    Build a serializer for the standard bulk response payload.

    Shape::

        {"items": [<item>, <item>, ...]}

    Wrap this in :func:`build_success_response_serializer` when documenting it
    on an ``@extend_schema(responses=...)`` declaration.
    """

    serializer_class = create_serializer_class(
        name=component_name,
        fields={items_field_name: item_serializer(many=True)},
    )
    return extend_schema_serializer(component_name=component_name)(serializer_class)


def build_bulk_ids_input_serializer(
    *,
    component_name: str,
    ids_field_name: str = "ids",
    min_items: int = DEFAULT_BULK_MIN_ITEMS,
    max_items: int = DEFAULT_BULK_MAX_ITEMS,
) -> type[serializers.Serializer]:
    """
    Build a serializer for a bulk request that only carries a list of UUIDs.

    Shape::

        {"ids": ["<uuid>", "<uuid>", ...]}

    Useful for bulk delete / restore / hard-delete and any other action that
    targets existing rows by primary key. Length is enforced via DRF's
    ``ListField`` (``min_length`` / ``max_length`` / ``allow_empty=False``) so
    individual APIs do not re-implement these checks.
    """

    ids_field = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        min_length=min_items,
        max_length=max_items,
    )
    serializer_class = create_serializer_class(
        name=component_name,
        fields={ids_field_name: ids_field},
    )
    return extend_schema_serializer(component_name=component_name)(serializer_class)
