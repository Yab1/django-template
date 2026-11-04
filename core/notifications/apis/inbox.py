from typing import Any, cast
from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response

from core.api.pagination import LimitOffsetPagination, get_paginated_response
from core.api.serializers import build_paginated_result_serializer, build_success_response_serializer
from core.api.views import AuthorizedAPIView
from core.notifications.constants import OPENAPI_TAG_NOTIFICATIONS
from core.notifications.selectors import notification_inbox_list, notification_unread_count
from core.notifications.serializers import (
    NotificationDeliveryModelSerializer,
    NotificationInboxQuerySerializer,
    ReadAllOutputSerializer,
    UnreadCountSerializer,
)
from core.notifications.services import notification_mark_read, notification_mark_read_all


class NotificationInboxListApi(AuthorizedAPIView):
    """Sent in-app notifications for the current user."""

    class Pagination(LimitOffsetPagination):
        default_limit = 25
        max_limit = 100

    QuerySerializer = NotificationInboxQuerySerializer
    PaginatedResultSerializer = build_paginated_result_serializer(
        component_name="NotificationInboxPaginatedResult",
        item_serializer=NotificationDeliveryModelSerializer,
    )
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="NotificationInboxSuccessResponse",
        result_serializer=PaginatedResultSerializer,
    )

    @extend_schema(
        operation_id="notifications_inbox_list",
        tags=[OPENAPI_TAG_NOTIFICATIONS],
        parameters=[QuerySerializer],
        responses={200: SuccessResponseSerializer},
        summary="List in-app inbox",
    )
    def get(self, request) -> Response:
        query = self.QuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        data = cast(dict[str, Any], query.validated_data)
        queryset = notification_inbox_list(user=request.user, unread=bool(data.get("unread")))
        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=NotificationDeliveryModelSerializer,
            queryset=queryset,
            request=request,
            view=self,
        )


class NotificationUnreadCountApi(AuthorizedAPIView):
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="NotificationUnreadCountSuccessResponse",
        result_serializer=UnreadCountSerializer,
    )

    @extend_schema(
        operation_id="notifications_unread_count",
        tags=[OPENAPI_TAG_NOTIFICATIONS],
        responses={200: SuccessResponseSerializer},
        summary="Unread in-app count",
    )
    def get(self, request) -> Response:
        return Response({"unread": notification_unread_count(user=request.user)}, status=status.HTTP_200_OK)


class NotificationReadAllApi(AuthorizedAPIView):
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="NotificationReadAllSuccessResponse",
        result_serializer=ReadAllOutputSerializer,
    )

    @extend_schema(
        operation_id="notifications_read_all",
        tags=[OPENAPI_TAG_NOTIFICATIONS],
        responses={200: SuccessResponseSerializer},
        summary="Mark all in-app notifications read",
    )
    def post(self, request) -> Response:
        updated = notification_mark_read_all(user=request.user)
        return Response({"updated": updated}, status=status.HTTP_200_OK)


class NotificationReadApi(AuthorizedAPIView):
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="NotificationReadSuccessResponse",
        result_serializer=NotificationDeliveryModelSerializer,
    )

    @extend_schema(
        operation_id="notifications_read",
        tags=[OPENAPI_TAG_NOTIFICATIONS],
        responses={200: SuccessResponseSerializer},
        summary="Mark one in-app notification read",
    )
    def post(self, request, notification_id: UUID) -> Response:
        row = notification_mark_read(user=request.user, notification_id=notification_id)
        return Response(NotificationDeliveryModelSerializer(row).data, status=status.HTTP_200_OK)
