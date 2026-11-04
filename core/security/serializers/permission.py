from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers


@extend_schema_serializer(component_name="PermissionOutput")
class PermissionOutputSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    reference_id = serializers.CharField()
    code = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class PermissionListQuerySerializer(serializers.Serializer):
    code = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    order_by = serializers.ChoiceField(
        required=False,
        choices=["code", "-code", "name", "-name", "created_at", "-created_at"],
    )
    limit = serializers.IntegerField(required=False, min_value=1, max_value=200)
    offset = serializers.IntegerField(required=False, min_value=0)
