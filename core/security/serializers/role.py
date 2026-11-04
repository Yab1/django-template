from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from core.security.serializers.permission import PermissionOutputSerializer


@extend_schema_serializer(component_name="RoleOutput")
class RoleOutputSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    reference_id = serializers.CharField()
    code = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    is_visible = serializers.BooleanField()
    permissions = PermissionOutputSerializer(many=True)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


@extend_schema_serializer(component_name="RoleCreateInput")
class RoleCreateInputSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    permission_codes = serializers.ListField(
        child=serializers.CharField(max_length=128),
        required=False,
        default=list,
    )


@extend_schema_serializer(component_name="RoleUpdateInput")
class RoleUpdateInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    is_visible = serializers.BooleanField(required=False)
    metadata = serializers.JSONField(required=False)
    permission_codes = serializers.ListField(
        child=serializers.CharField(max_length=128),
        required=False,
    )


class RoleListQuerySerializer(serializers.Serializer):
    code = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    is_visible = serializers.BooleanField(required=False)
    order_by = serializers.ChoiceField(
        required=False,
        choices=["code", "-code", "name", "-name", "created_at", "-created_at"],
    )
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100)
    offset = serializers.IntegerField(required=False, min_value=0)
