from typing import Any, cast
from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response

from core.api.pagination import LimitOffsetPagination, get_paginated_response
from core.api.serializers import build_paginated_result_serializer, build_success_response_serializer
from core.api.utils import cache_api_response, run_service
from core.api.views import AuthorizedAPIView
from core.users.constants import OPENAPI_TAG_USERS
from core.users.selectors import user_list
from core.users.serializers import (
    UserListQuerySerializer,
    UserListSerializer,
    UserUpdateInputSerializer,
    UserUpdateOutputSerializer,
)
from core.users.services import user_update


class UserListApi(AuthorizedAPIView):
    """Paginated list of user accounts."""

    authorization_resource_code = "User"
    authorization_action = "users:user:list"

    class Pagination(LimitOffsetPagination):
        default_limit = 25
        max_limit = 100

    QuerySerializer = UserListQuerySerializer
    PaginatedResultSerializer = build_paginated_result_serializer(
        component_name="UserListPaginatedResult",
        item_serializer=UserListSerializer,
    )
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="UserListSuccessResponse",
        result_serializer=PaginatedResultSerializer,
    )

    @extend_schema(
        operation_id="users_list",
        tags=[OPENAPI_TAG_USERS],
        parameters=[QuerySerializer],
        responses={200: SuccessResponseSerializer},
        description="List user accounts.",
        summary="List users",
    )
    @cache_api_response(namespace="user:list")
    def get(self, request) -> Response:
        query_serializer = self.QuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        queryset = user_list(
            filters=cast(dict[str, Any], query_serializer.validated_data),
            requesting_user=request.user,
        )

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=UserListSerializer,
            queryset=queryset,
            request=request,
            view=self,
        )


class UserUpdateApi(AuthorizedAPIView):
    """Update account fields for a user by id."""

    authorization_resource_code = "User"
    authorization_action = "users:user:update"

    InputSerializer = UserUpdateInputSerializer
    OutputSerializer = UserUpdateOutputSerializer

    SuccessResponseSerializer = build_success_response_serializer(
        component_name="UserUpdateSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="users_user_update",
        tags=[OPENAPI_TAG_USERS],
        request=InputSerializer,
        responses={200: SuccessResponseSerializer},
        description="Partially update a user account. Password changes use other endpoints.",
        summary="Update user by id",
    )
    def patch(self, request, id: UUID) -> Response:
        serializer = self.InputSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        obj = run_service(
            user_update,
            serializer.validated_data,
            id=id,
            _as="data",
            requesting_user=request.user,
        )
        return Response(data=self.OutputSerializer(obj).data, status=status.HTTP_200_OK)
