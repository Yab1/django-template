from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from core.security.serializers.role import RoleOutputSerializer


@extend_schema_serializer(component_name="UserRoleOutput")
class UserRoleOutputSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    role = RoleOutputSerializer()
    assigned_by_id = serializers.UUIDField(allow_null=True)
    created_at = serializers.DateTimeField()


@extend_schema_serializer(component_name="UserRoleAssignInput")
class UserRoleAssignInputSerializer(serializers.Serializer):
    role_id = serializers.UUIDField()


@extend_schema_serializer(component_name="MePermissionsOutput")
class MePermissionsOutputSerializer(serializers.Serializer):
    codes = serializers.ListField(child=serializers.CharField())
    roles = serializers.ListField(child=serializers.CharField())
    is_superuser = serializers.BooleanField()
