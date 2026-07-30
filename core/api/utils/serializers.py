"""Dynamic DRF serializer helpers for OpenAPI schema generation."""

from typing import Any

from rest_framework import serializers


def create_serializer_class(*, name: str, fields: dict[str, Any]) -> type[serializers.Serializer]:
    return type(name, (serializers.Serializer,), fields)


def inline_serializer(
    *,
    fields: dict[str, Any],
    name: str = "InlineSerializer",
    **kwargs: Any,
) -> serializers.BaseSerializer:
    inner_class = create_serializer_class(name=name, fields=fields)
    return inner_class(**kwargs)
