# pyright: reportOptionalMemberAccess=false
# pyright: reportAssignmentType=false

from typing import Any, cast

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema_serializer
from rest_framework import serializers as _s
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer, TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings

from core.authentication.services import login_event_failed_record, login_event_logout_record
from core.users.constants import PASSWORD_MAX_LENGTH
from core.users.serializers import UserCompactSerializer


@extend_schema_serializer(component_name="MeUserOutput")
class MeUserOutputSerializer(UserCompactSerializer):
    phone_number = _s.IntegerField()
    is_active = _s.BooleanField()
    is_staff = _s.BooleanField()
    is_admin = _s.BooleanField()
    is_superuser = _s.BooleanField()
    must_change_password = _s.BooleanField(
        help_text=(
            "True when the account was provisioned with a temporary password. "
            "Redirect to the set-password page when this is true."
        )
    )


@extend_schema_serializer(component_name="MeOutput")
class MeOutputSerializer(_s.Serializer):
    user = MeUserOutputSerializer()


@extend_schema_serializer(component_name="CurrentUserPasswordChangeInput")
class CurrentUserPasswordChangeInputSerializer(_s.Serializer):
    current_password = _s.CharField(
        write_only=True,
        required=True,
        allow_blank=False,
        max_length=PASSWORD_MAX_LENGTH,
    )
    new_password = _s.CharField(
        write_only=True,
        min_length=1,
        max_length=PASSWORD_MAX_LENGTH,
    )

    def validate_new_password(self, value: str) -> str:
        user = self.context["request"].user
        try:
            validate_password(value, user)
        except DjangoValidationError as exc:
            if hasattr(exc, "error_dict"):
                raise _s.ValidationError(detail=dict(exc.message_dict)) from exc
            raise _s.ValidationError(detail=list(exc.messages)) from exc
        return value


@extend_schema_serializer(component_name="CurrentUserPasswordChangeOutput")
class CurrentUserPasswordChangeOutputSerializer(_s.Serializer):
    updated = _s.BooleanField()


@extend_schema_serializer(component_name="PasswordResetConfirmInput")
class PasswordResetConfirmInputSerializer(_s.Serializer):
    uid = _s.CharField(
        required=True,
        write_only=True,
        help_text="URL-safe base64-encoded user primary key (from reset link).",
    )
    token = _s.CharField(
        required=True,
        write_only=True,
        help_text="One-time reset token (from reset link). Invalidated once used.",
    )
    new_password = _s.CharField(
        required=True,
        write_only=True,
        max_length=PASSWORD_MAX_LENGTH,
        help_text="New password. Must satisfy the configured Django password policy.",
    )

    def validate_new_password(self, value: str) -> str:
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            if hasattr(exc, "error_dict"):
                raise _s.ValidationError(detail=dict(exc.message_dict)) from exc
            raise _s.ValidationError(detail=list(exc.messages)) from exc
        return value


@extend_schema_serializer(component_name="PasswordResetConfirmOutput")
class PasswordResetConfirmOutputSerializer(_s.Serializer):
    password_set = _s.BooleanField(
        help_text="True when the new password was accepted and must_change_password was cleared."
    )


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Same as SimpleJWT's pair serializer, but emits ``user_logged_in`` on success
    and adds ``id``, ``username``, and ``email`` to the response body (alongside
    ``refresh`` and ``access``).

    django-easy-audit records successful logins from ``user_logged_in``; session-based
    admin login triggers it via ``django.contrib.auth.login()``, while JWT obtain does not,
    so we send the signal explicitly for API logins.

    Failed JWT authentication raises ``AuthenticationFailed`` without a reliable
    ``LoginEvent`` row from easy-audit's ``user_login_failed`` handler (it depends on
    ``get_current_request()``), so we write a ``LoginEvent.FAILED`` row explicitly.

    Credential field name follows ``User.USERNAME_FIELD`` (``username``).
    """

    def validate(self, attrs):
        username_field = self.username_field
        username_attempt = str(attrs.get(username_field) or "")
        request = self.context.get("request")
        try:
            data = cast(dict[str, Any], super().validate(attrs))
        except AuthenticationFailed:
            login_event_failed_record(username=username_attempt, request=request)
            raise
        if request is not None:
            user_logged_in.send(sender=self.user.__class__, request=request, user=self.user)
        user = self.user
        data["id"] = user.pk
        data["username"] = user.username
        data["email"] = user.email
        return data


class CustomTokenBlacklistSerializer(TokenBlacklistSerializer):
    """Blacklist refresh token and record a django-easy-audit logout row."""

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        request = self.context.get("request")
        refresh = self.token_class(attrs["refresh"])
        user_id = refresh.payload.get(api_settings.USER_ID_CLAIM)
        user = None
        if user_id is not None:
            User = get_user_model()  # noqa: N806
            try:
                user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
            except User.DoesNotExist:
                user = None
        data = super().validate(attrs)
        if user is not None:
            login_event_logout_record(user=user, request=request)  # pyright: ignore[reportArgumentType]
        return data
