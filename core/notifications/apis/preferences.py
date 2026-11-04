from typing import Any, cast

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response

from core.api.serializers import build_success_response_serializer
from core.api.views import AuthorizedAPIView
from core.notifications.constants import OPENAPI_TAG_NOTIFICATIONS
from core.notifications.selectors import notification_preference_effective, notification_preference_list
from core.notifications.serializers import (
    NotificationPreferenceEffectiveSerializer,
    NotificationPreferenceSerializer,
    NotificationPreferenceUpsertInputSerializer,
)
from core.notifications.services import notification_preference_upsert


class NotificationPreferenceListApi(AuthorizedAPIView):
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="NotificationPreferenceListSuccessResponse",
        result_serializer=NotificationPreferenceSerializer,
    )

    @extend_schema(
        operation_id="notification_preferences_list",
        tags=[OPENAPI_TAG_NOTIFICATIONS],
        responses={200: SuccessResponseSerializer},
        summary="Stored notification preferences",
    )
    def get(self, request) -> Response:
        rows = notification_preference_list(user=request.user)
        return Response(NotificationPreferenceSerializer(rows, many=True).data, status=status.HTTP_200_OK)


class NotificationPreferenceEffectiveApi(AuthorizedAPIView):
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="NotificationPreferenceEffectiveSuccessResponse",
        result_serializer=NotificationPreferenceEffectiveSerializer,
    )

    @extend_schema(
        operation_id="notification_preferences_effective",
        tags=[OPENAPI_TAG_NOTIFICATIONS],
        responses={200: SuccessResponseSerializer},
        summary="Effective preference matrix",
    )
    def get(self, request) -> Response:
        items = notification_preference_effective(user=request.user)
        return Response(NotificationPreferenceEffectiveSerializer(items, many=True).data, status=status.HTTP_200_OK)


class NotificationPreferenceUpsertApi(AuthorizedAPIView):
    InputSerializer = NotificationPreferenceUpsertInputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="NotificationPreferenceUpsertSuccessResponse",
        result_serializer=NotificationPreferenceSerializer,
    )

    @extend_schema(
        operation_id="notification_preferences_upsert",
        tags=[OPENAPI_TAG_NOTIFICATIONS],
        request=InputSerializer,
        responses={200: SuccessResponseSerializer},
        summary="Upsert notification preferences",
    )
    def put(self, request) -> Response:
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)
        rows = notification_preference_upsert(user=request.user, items=data["items"])
        return Response(NotificationPreferenceSerializer(rows, many=True).data, status=status.HTTP_200_OK)
