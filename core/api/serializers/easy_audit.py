"""Shared serializers for django-easy-audit ``CRUDEvent`` / ``LoginEvent`` list APIs."""

import json
import logging
from typing import Any

from drf_spectacular.utils import extend_schema_serializer
from easyaudit.models import CRUDEvent, LoginEvent
from rest_framework import serializers

from core.api.utils import inline_serializer
from core.common.enums import (
    CrudEventType,
    LoginEventType,
    crud_event_type_to_int,
    int_to_crud_event_type,
    int_to_login_event_type,
    login_event_type_to_int,
)
from core.users.selectors.user import user_profile_full_name, user_profile_primary_photo
from core.users.serializers import UserCompactSerializer

logger = logging.getLogger(__name__)


def _user_compact_or_none(user: Any) -> dict[str, Any] | None:
    """Shape a ``User`` (or None) for ``UserCompactSerializer`` output."""
    if user is None:
        return None
    photo = user_profile_primary_photo(user=user)
    primary_photo = None
    if photo is not None:
        from core.common.data_types.serializers import AttachmentOutputSerializer

        primary_photo = AttachmentOutputSerializer(photo).data
    return {
        "id": user.pk,
        "username": user.username,
        "email": user.email,
        "full_name": user_profile_full_name(user=user),
        "primary_photo": primary_photo,
    }


def _parse_stored_json(value: str | None) -> Any | None:
    """
    Turn easy-audit DB text (JSON) into Python values for API responses.

    Empty or whitespace-only strings become ``None``. Invalid JSON is logged and becomes
    ``None`` so the response stays valid JSON (no raw string blobs for these keys).
    """
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        logger.warning(
            "easyaudit stored JSON could not be decoded; returning null",
            extra={"snippet": stripped[:200]},
        )
        return None


def crud_event_to_representation(event: CRUDEvent) -> dict[str, Any]:
    """Shape one ``easyaudit.models.CRUDEvent`` for API responses."""
    ct = event.content_type
    try:
        event_type_str = int_to_crud_event_type(event.event_type)
        event_type_label = str(CrudEventType(event_type_str).label)
    except (KeyError, ValueError):
        event_type_str = str(event.event_type)
        event_type_label = str(dict(CRUDEvent.TYPES).get(event.event_type, ""))
    return {
        "id": event.pk,
        "event_type": event_type_str,
        "event_type_label": event_type_label,
        "object_id": event.object_id,
        "content_type_id": ct.pk,
        "content_type": {"app_label": ct.app_label, "model": ct.model},
        "object_repr": event.object_repr,
        "object_json_repr": _parse_stored_json(event.object_json_repr),
        "changed_fields": _parse_stored_json(event.changed_fields),
        "user": _user_compact_or_none(getattr(event, "user", None)),
        "datetime": event.datetime,
    }


@extend_schema_serializer(component_name="CrudEventOutputSerializer")
class CrudEventOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    event_type = serializers.CharField()
    event_type_label = serializers.CharField()
    object_id = serializers.CharField()
    content_type_id = serializers.IntegerField()
    content_type = inline_serializer(
        fields={
            "app_label": serializers.CharField(),
            "model": serializers.CharField(),
        }
    )
    object_repr = serializers.CharField(required=False, allow_blank=True)
    object_json_repr = serializers.JSONField(required=False, allow_null=True)
    changed_fields = serializers.JSONField(required=False, allow_null=True)
    user = UserCompactSerializer(allow_null=True, required=False)
    datetime = serializers.DateTimeField()

    def to_representation(self, instance: Any) -> dict[str, Any]:
        if isinstance(instance, CRUDEvent):
            return crud_event_to_representation(instance)
        return super().to_representation(instance)


@extend_schema_serializer(component_name="CrudEventAuditListFilterSerializer")
class CrudEventAuditListFilterSerializer(serializers.Serializer):
    event_type = serializers.ChoiceField(choices=CrudEventType.choices, required=False)
    user_id = serializers.UUIDField(required=False)
    datetime_from = serializers.DateTimeField(required=False)
    datetime_to = serializers.DateTimeField(required=False)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        event_type = attrs.get("event_type")
        if event_type:
            attrs["event_type"] = crud_event_type_to_int(str(event_type))
        return attrs


def login_event_to_representation(event: LoginEvent) -> dict[str, Any]:
    """Shape one ``easyaudit.models.LoginEvent`` for API responses."""
    try:
        login_type_str = int_to_login_event_type(event.login_type)
        login_type_label = str(LoginEventType(login_type_str).label)
    except (KeyError, ValueError):
        login_type_str = str(event.login_type)
        login_type_label = str(dict(LoginEvent.TYPES).get(event.login_type, ""))
    return {
        "id": event.pk,
        "login_type": login_type_str,
        "login_type_label": login_type_label,
        "username": event.username,
        "user": _user_compact_or_none(getattr(event, "user", None)),
        "remote_ip": event.remote_ip,
        "datetime": event.datetime,
    }


@extend_schema_serializer(component_name="LoginEventOutputSerializer")
class LoginEventOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    login_type = serializers.CharField()
    login_type_label = serializers.CharField()
    username = serializers.CharField(required=False, allow_blank=True)
    user = UserCompactSerializer(allow_null=True, required=False)
    remote_ip = serializers.CharField(required=False, allow_blank=True)
    datetime = serializers.DateTimeField()

    def to_representation(self, instance: Any) -> dict[str, Any]:
        if isinstance(instance, LoginEvent):
            return login_event_to_representation(instance)
        return super().to_representation(instance)


@extend_schema_serializer(component_name="UserLoginEventListQuery")
class LoginEventListQuerySerializer(serializers.Serializer):
    login_type = serializers.ChoiceField(choices=LoginEventType.choices, required=False)
    username = serializers.CharField(required=False)
    datetime_from = serializers.DateTimeField(required=False)
    datetime_to = serializers.DateTimeField(required=False)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
    offset = serializers.IntegerField(required=False, min_value=0, default=0)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        login_type = attrs.get("login_type")
        if login_type:
            attrs["login_type"] = login_event_type_to_int(str(login_type))
        return attrs
