"""Reusable OpenAPI serializers for documented response shapes."""

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from core.api.utils.serializers import create_serializer_class


@extend_schema_serializer(component_name="SuccessMetaSerializer")
class SuccessMetaSerializer(serializers.Serializer):
    """Static metadata present on successful API responses."""

    version = serializers.CharField()


def build_paginated_result_serializer(
    *,
    component_name: str,
    item_serializer: type[serializers.Serializer],
) -> type[serializers.Serializer]:
    """
    Build a serializer for paginated ``result`` payloads.

    Shape:
        {
            "limit": 10,
            "offset": 0,
            "count": 25,
            "next": null,
            "previous": null,
            "results": [...]
        }
    """

    serializer_class = create_serializer_class(
        name=component_name,
        fields={
            "limit": serializers.IntegerField(),
            "offset": serializers.IntegerField(),
            "count": serializers.IntegerField(),
            "next": serializers.URLField(required=False, allow_null=True),
            "previous": serializers.URLField(required=False, allow_null=True),
            "results": item_serializer(many=True),
        },
    )
    return extend_schema_serializer(component_name=component_name)(serializer_class)


def build_success_response_serializer(
    *,
    component_name: str,
    result_serializer: type[serializers.Serializer],
) -> type[serializers.Serializer]:
    """
    Build a serializer for the standard successful response envelope.

    Shape:
        {
            "status": "success",
            "result": {...},
            "meta": {"version": "v1"},
            "message": "Request processed successfully"
        }
    """

    serializer_class = create_serializer_class(
        name=component_name,
        fields={
            "status": serializers.ChoiceField(choices=["success"]),
            "result": result_serializer(),
            "meta": SuccessMetaSerializer(),
            "message": serializers.CharField(),
        },
    )
    return extend_schema_serializer(component_name=component_name)(serializer_class)


def build_error_response_serializer(
    *,
    component_name: str,
    result_serializer: type[serializers.Serializer],
) -> type[serializers.Serializer]:
    """
    Build a serializer for the standard error response envelope (same keys as success).

    Shape:
        {
            "status": "error",
            "result": {...},
            "meta": {"version": "v1"},
            "message": "..."
        }
    """

    serializer_class = create_serializer_class(
        name=component_name,
        fields={
            "status": serializers.ChoiceField(choices=["error"]),
            "result": result_serializer(),
            "meta": SuccessMetaSerializer(),
            "message": serializers.CharField(),
        },
    )
    return extend_schema_serializer(component_name=component_name)(serializer_class)
