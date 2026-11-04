from typing import Any, cast

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response

from core.api.serializers import build_success_response_serializer
from core.api.views import AuthorizedAPIView
from core.notifications.constants import OPENAPI_TAG_NOTIFICATIONS
from core.notifications.serializers import NotificationDeliveryModelSerializer, NotificationSendInputSerializer
from core.notifications.services import notification_notify
from core.users.models import User


class NotificationSendApi(AuthorizedAPIView):
    """Admin: enqueue and dispatch a notification to a user."""

    authorization_resource_code = "Notification"
    authorization_action = "notifications:send"

    InputSerializer = NotificationSendInputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="NotificationSendSuccessResponse",
        result_serializer=NotificationDeliveryModelSerializer,
    )

    @extend_schema(
        operation_id="notifications_send",
        tags=[OPENAPI_TAG_NOTIFICATIONS],
        request=InputSerializer,
        responses={201: SuccessResponseSerializer},
        summary="Send a notification (admin)",
    )
    def post(self, request) -> Response:
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)
        user = get_object_or_404(User, pk=data["user_id"])
        rows = notification_notify(
            user=user,
            category=data["category"],
            event_code=data.get("event_code") or "admin.send",
            data=data.get("data") or {},
            channels=data.get("channels"),
            idempotency_key=data.get("idempotency_key") or None,
            resource_type=data.get("resource_type") or "",
            resource_id=data.get("resource_id"),
        )
        return Response(NotificationDeliveryModelSerializer(rows, many=True).data, status=status.HTTP_201_CREATED)
