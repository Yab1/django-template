"""Revision block on resource detail responses (django-simple-history latest row)."""

from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from core.users.serializers import UserCompactSerializer


@extend_schema_serializer(component_name="RevisionSerializer")
class RevisionSerializer(serializers.Serializer):
    """
    Latest audit snapshot for a resource detail response (from ``revision_payload_for_latest``).
    ``type`` is the raw django-simple-history code (+, ~, -).
    """

    id = serializers.IntegerField(source="history_id")
    total = serializers.IntegerField(min_value=1)
    type = serializers.CharField(source="history_type")
    is_latest = serializers.BooleanField()
    recorded_at = serializers.DateTimeField(source="history_date")
    change_reason = serializers.CharField(source="history_change_reason")
    user = UserCompactSerializer(source="history_user", allow_null=True)
