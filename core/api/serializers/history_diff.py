"""Shared DRF serializers for django-simple-history diff (OpenAPI + shared ``result`` shape)."""

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from core.api.utils.serializers import inline_serializer
from core.users.serializers import UserCompactSerializer


@extend_schema_serializer(component_name="HistoryListItemSerializer")
class HistoryListItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="history_id")
    recorded_at = serializers.DateTimeField(source="history_date")
    type = serializers.CharField(source="history_type")
    change_reason = serializers.CharField(source="history_change_reason")
    user = UserCompactSerializer(source="history_user")


@extend_schema_serializer(component_name="HistoryDiffResponseSerializer")
class HistoryDiffResponseSerializer(serializers.Serializer):
    """
    drf-spectacular / OpenAPI — runtime payloads use ``model_delta_to_api_dict`` in ``core.api.utils.model_delta``.
    Use on every ``*HistoryDiffApi`` so the diff ``result`` schema is defined once.
    """

    from_history_id = serializers.IntegerField()
    to_history_id = serializers.IntegerField()
    changed_fields = serializers.ListField(child=serializers.CharField())
    changes = inline_serializer(
        many=True,
        fields={
            "field": serializers.CharField(),
            "old": serializers.JSONField(allow_null=True),
            "new": serializers.JSONField(allow_null=True),
        },
    )
