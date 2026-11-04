from typing import Any, cast
from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response

from core.api.pagination import LimitOffsetPagination, get_paginated_response
from core.api.serializers import build_paginated_result_serializer, build_success_response_serializer
from core.api.views import AuthorizedAPIView
from core.notifications.constants import OPENAPI_TAG_NOTIFICATIONS
from core.notifications.selectors import notification_template_list
from core.notifications.serializers import NotificationTemplateSerializer, NotificationTemplateUpdateInputSerializer
from core.notifications.services import notification_template_update


class NotificationTemplateListApi(AuthorizedAPIView):
    authorization_resource_code = "Notification"
    authorization_action = "notifications:template:list"

    class Pagination(LimitOffsetPagination):
        default_limit = 50
        max_limit = 200

    PaginatedResultSerializer = build_paginated_result_serializer(
        component_name="NotificationTemplatePaginatedResult",
        item_serializer=NotificationTemplateSerializer,
    )
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="NotificationTemplateListSuccessResponse",
        result_serializer=PaginatedResultSerializer,
    )

    @extend_schema(
        operation_id="notification_templates_list",
        tags=[OPENAPI_TAG_NOTIFICATIONS],
        responses={200: SuccessResponseSerializer},
        summary="List notification templates (admin)",
    )
    def get(self, request) -> Response:
        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=NotificationTemplateSerializer,
            queryset=notification_template_list(),
            request=request,
            view=self,
        )


class NotificationTemplateUpdateApi(AuthorizedAPIView):
    authorization_resource_code = "Notification"
    authorization_action = "notifications:template:update"

    InputSerializer = NotificationTemplateUpdateInputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="NotificationTemplateUpdateSuccessResponse",
        result_serializer=NotificationTemplateSerializer,
    )

    @extend_schema(
        operation_id="notification_templates_update",
        tags=[OPENAPI_TAG_NOTIFICATIONS],
        request=InputSerializer,
        responses={200: SuccessResponseSerializer},
        summary="Update a notification template (admin)",
    )
    def patch(self, request, template_id: UUID) -> Response:
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        row = notification_template_update(
            template_id=template_id,
            data=cast(dict[str, Any], serializer.validated_data),
        )
        return Response(NotificationTemplateSerializer(row).data, status=status.HTTP_200_OK)
