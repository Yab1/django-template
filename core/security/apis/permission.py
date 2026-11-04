from typing import Any, cast
from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response

from core.api.pagination import LimitOffsetPagination, get_paginated_response
from core.api.serializers import build_paginated_result_serializer, build_success_response_serializer
from core.api.views import AuthorizedAPIView
from core.security.constants import OPENAPI_TAG_SECURITY
from core.security.selectors import permission_get, permission_list
from core.security.serializers import PermissionListQuerySerializer, PermissionOutputSerializer


class PermissionListApi(AuthorizedAPIView):
    authorization_resource_code = "Permission"
    authorization_action = "security:permission:list"

    class Pagination(LimitOffsetPagination):
        default_limit = 100
        max_limit = 200

    QuerySerializer = PermissionListQuerySerializer
    PaginatedResultSerializer = build_paginated_result_serializer(
        component_name="PermissionListPaginatedResult",
        item_serializer=PermissionOutputSerializer,
    )
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="PermissionListSuccessResponse",
        result_serializer=PaginatedResultSerializer,
    )

    @extend_schema(
        operation_id="security_permission_list",
        tags=[OPENAPI_TAG_SECURITY],
        parameters=[QuerySerializer],
        responses={200: SuccessResponseSerializer},
        summary="List permission catalog",
    )
    def get(self, request) -> Response:
        query = self.QuerySerializer(data=request.query_params.dict())
        query.is_valid(raise_exception=True)
        queryset = permission_list(filters=cast(dict[str, Any], query.validated_data))
        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=PermissionOutputSerializer,
            queryset=queryset,
            request=request,
            view=self,
        )


class PermissionGetApi(AuthorizedAPIView):
    authorization_resource_code = "Permission"
    authorization_action = "security:permission:get"

    OutputSerializer = PermissionOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="PermissionGetSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="security_permission_get",
        tags=[OPENAPI_TAG_SECURITY],
        responses={200: SuccessResponseSerializer},
        summary="Get permission",
    )
    def get(self, request, id: UUID) -> Response:
        obj = permission_get(permission_id=id)
        return Response(self.OutputSerializer(obj).data, status=status.HTTP_200_OK)
