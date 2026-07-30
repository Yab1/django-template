from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers

from core.users.constants import PASSWORD_MAX_LENGTH


@extend_schema_serializer(component_name="UserCompact")
class UserCompactSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.EmailField()


@extend_schema_serializer(component_name="UserListItem")
class UserListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.IntegerField()
    is_active = serializers.BooleanField()
    is_staff = serializers.BooleanField()
    is_admin = serializers.BooleanField()
    is_superuser = serializers.BooleanField()
    is_visible = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


@extend_schema_serializer(component_name="UserUpdateInput")
class UserUpdateInputSerializer(serializers.Serializer):
    username = serializers.CharField(required=False, allow_blank=False)
    email = serializers.EmailField(required=False)
    phone_number = serializers.IntegerField(required=False)
    is_active = serializers.BooleanField(required=False)
    is_staff = serializers.BooleanField(required=False)
    is_admin = serializers.BooleanField(required=False)
    is_superuser = serializers.BooleanField(required=False)
    is_visible = serializers.BooleanField(required=False)
    metadata = serializers.JSONField(required=False)


@extend_schema_serializer(component_name="UserUpdateOutput")
class UserUpdateOutputSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    username = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.IntegerField()
    is_active = serializers.BooleanField()
    is_staff = serializers.BooleanField()
    is_admin = serializers.BooleanField()
    is_superuser = serializers.BooleanField()
    is_visible = serializers.BooleanField()
    metadata = serializers.JSONField(required=False)
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


@extend_schema_serializer(component_name="UserPasswordResetInput")
class UserPasswordResetInputSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=1, max_length=PASSWORD_MAX_LENGTH, write_only=True)

    def validate_new_password(self, value: str) -> str:
        target = self.context["target_user"]
        try:
            validate_password(value, target)
        except DjangoValidationError as exc:
            if hasattr(exc, "error_dict"):
                raise serializers.ValidationError(detail=dict(exc.message_dict)) from exc
            raise serializers.ValidationError(detail=list(exc.messages)) from exc
        return value


@extend_schema_serializer(component_name="UserPasswordResetOutput")
class UserPasswordResetOutputSerializer(serializers.Serializer):
    updated = serializers.BooleanField()


class UserListQuerySerializer(serializers.Serializer):
    is_visible = serializers.BooleanField(required=False, default=True)
    is_deleted = serializers.BooleanField(required=False, default=False)
    email = serializers.CharField(required=False)
    order_by = serializers.ChoiceField(
        required=False,
        choices=[
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
            "deleted_at",
            "-deleted_at",
            "email",
            "-email",
        ],
        help_text="Sort by field. Prefix with '-' for descending.",
    )
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100, default=25)
    offset = serializers.IntegerField(required=False, min_value=0, default=0)
