from typing import Any, cast
from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response

from core.api.pagination import LimitOffsetPagination, get_paginated_response
from core.api.serializers import build_paginated_result_serializer, build_success_response_serializer
from core.api.views import AuthorizedAPIView
from core.notifications.constants import OPENAPI_TAG_NOTIFICATIONS
from core.notifications.selectors import notification_delivery_get, notification_delivery_list
from core.notifications.serializers import (
    NotificationDeliveryListQuerySerializer,
    NotificationDeliveryModelSerializer,
)
from core.notifications.serializers.delivery import NotificationAttemptModelSerializer
from core.notifications.services import notification_delivery_retry


class NotificationDeliveryDetailOutputSerializer(NotificationDeliveryModelSerializer):
    attempt_log = NotificationAttemptModelSerializer(many=True)

    class Meta(NotificationDeliveryModelSerializer.Meta):
        fields = (*NotificationDeliveryModelSerializer.Meta.fields, "attempt_log")


class NotificationDeliveryListApi(AuthorizedAPIView):
    authorization_resource_code = "Notification"
    authorization_action = "notifications:delivery:list"

    class Pagination(LimitOffsetPagination):
        default_limit = 25
        max_limit = 100

    QuerySerializer = NotificationDeliveryListQuerySerializer
    PaginatedResultSerializer = build_paginated_result_serializer(
        component_name="NotificationDeliveryPaginatedResult",
        item_serializer=NotificationDeliveryModelSerializer,
    )
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="NotificationDeliveryListSuccessResponse",
        result_serializer=PaginatedResultSerializer,
    )

    @extend_schema(
        operation_id="notification_deliveries_list",
        tags=[OPENAPI_TAG_NOTIFICATIONS],
        parameters=[QuerySerializer],
        responses={200: SuccessResponseSerializer},
        summary="List all deliveries (admin)",
    )
    def get(self, request) -> Response:
        query = self.QuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        queryset = notification_delivery_list(filters=cast(dict[str, Any], query.validated_data))
        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=NotificationDeliveryModelSerializer,
            queryset=queryset,
            request=request,
            view=self,
        )


class NotificationDeliveryGetApi(AuthorizedAPIView):
    authorization_resource_code = "Notification"
    authorization_action = "notifications:delivery:get"

    SuccessResponseSerializer = build_success_response_serializer(
        component_name="NotificationDeliveryGetSuccessResponse",
        result_serializer=NotificationDeliveryDetailOutputSerializer,
    )

    @extend_schema(
        operation_id="notification_deliveries_get",
        tags=[OPENAPI_TAG_NOTIFICATIONS],
        responses={200: SuccessResponseSerializer},
        summary="Delivery detail with attempts (admin)",
    )
    def get(self, request, notification_id: UUID) -> Response:
        row = notification_delivery_get(delivery_id=notification_id)
        return Response(NotificationDeliveryDetailOutputSerializer(row).data, status=status.HTTP_200_OK)


class NotificationDeliveryRetryApi(AuthorizedAPIView):
    authorization_resource_code = "Notification"
    authorization_action = "notifications:delivery:retry"

    SuccessResponseSerializer = build_success_response_serializer(
        component_name="NotificationDeliveryRetrySuccessResponse",
        result_serializer=NotificationDeliveryModelSerializer,
    )

    @extend_schema(
        operation_id="notification_deliveries_retry",
        tags=[OPENAPI_TAG_NOTIFICATIONS],
        responses={200: SuccessResponseSerializer},
        summary="Retry a failed delivery (admin)",
    )
    def post(self, request, notification_id: UUID) -> Response:
        row = notification_delivery_retry(delivery_id=notification_id)
        return Response(NotificationDeliveryModelSerializer(row).data, status=status.HTTP_200_OK)
