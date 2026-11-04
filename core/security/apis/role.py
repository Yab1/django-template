from typing import Any, cast
from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response

from core.api.pagination import LimitOffsetPagination, get_paginated_response
from core.api.serializers import build_paginated_result_serializer, build_success_response_serializer
from core.api.views import AuthorizedAPIView
from core.security.constants import OPENAPI_TAG_SECURITY
from core.security.selectors import role_get, role_list
from core.security.serializers import (
    RoleCreateInputSerializer,
    RoleListQuerySerializer,
    RoleOutputSerializer,
    RoleUpdateInputSerializer,
)
from core.security.services import role_create, role_delete, role_update


class RoleCreateApi(AuthorizedAPIView):
    authorization_resource_code = "Role"
    authorization_action = "security:role:create"

    InputSerializer = RoleCreateInputSerializer
    OutputSerializer = RoleOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="RoleCreateSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="security_role_create",
        tags=[OPENAPI_TAG_SECURITY],
        request=InputSerializer,
        responses={201: SuccessResponseSerializer},
        summary="Create role",
    )
    def post(self, request) -> Response:
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)
        obj = role_create(
            code=data["code"],
            name=data["name"],
            description=data.get("description", ""),
            permission_codes=data.get("permission_codes") or [],
        )
        obj = role_get(role_id=obj.id)
        return Response(self.OutputSerializer(obj).data, status=status.HTTP_201_CREATED)


class RoleListApi(AuthorizedAPIView):
    authorization_resource_code = "Role"
    authorization_action = "security:role:list"

    class Pagination(LimitOffsetPagination):
        default_limit = 25
        max_limit = 100

    QuerySerializer = RoleListQuerySerializer
    PaginatedResultSerializer = build_paginated_result_serializer(
        component_name="RoleListPaginatedResult",
        item_serializer=RoleOutputSerializer,
    )
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="RoleListSuccessResponse",
        result_serializer=PaginatedResultSerializer,
    )

    @extend_schema(
        operation_id="security_role_list",
        tags=[OPENAPI_TAG_SECURITY],
        parameters=[QuerySerializer],
        responses={200: SuccessResponseSerializer},
        summary="List roles",
    )
    def get(self, request) -> Response:
        query = self.QuerySerializer(data=request.query_params.dict())
        query.is_valid(raise_exception=True)
        queryset = role_list(filters=cast(dict[str, Any], query.validated_data))
        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=RoleOutputSerializer,
            queryset=queryset,
            request=request,
            view=self,
        )


class RoleGetApi(AuthorizedAPIView):
    authorization_resource_code = "Role"
    authorization_action = "security:role:get"

    OutputSerializer = RoleOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="RoleGetSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="security_role_get",
        tags=[OPENAPI_TAG_SECURITY],
        responses={200: SuccessResponseSerializer},
        summary="Get role",
    )
    def get(self, request, id: UUID) -> Response:
        obj = role_get(role_id=id)
        return Response(self.OutputSerializer(obj).data, status=status.HTTP_200_OK)


class RoleUpdateApi(AuthorizedAPIView):
    authorization_resource_code = "Role"
    authorization_action = "security:role:update"

    InputSerializer = RoleUpdateInputSerializer
    OutputSerializer = RoleOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="RoleUpdateSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="security_role_update",
        tags=[OPENAPI_TAG_SECURITY],
        request=InputSerializer,
        responses={200: SuccessResponseSerializer},
        summary="Update role",
    )
    def patch(self, request, id: UUID) -> Response:
        serializer = self.InputSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        role_update(role_id=id, data=cast(dict[str, Any], serializer.validated_data))
        obj = role_get(role_id=id)
        return Response(self.OutputSerializer(obj).data, status=status.HTTP_200_OK)


class RoleDeleteApi(AuthorizedAPIView):
    authorization_resource_code = "Role"
    authorization_action = "security:role:delete"

    OutputSerializer = RoleOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="RoleDeleteSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="security_role_delete",
        tags=[OPENAPI_TAG_SECURITY],
        responses={200: SuccessResponseSerializer},
        summary="Delete role",
    )
    def delete(self, request, id: UUID) -> Response:
        obj = role_delete(role_id=id, requesting_user=request.user)
        return Response(self.OutputSerializer(obj).data, status=status.HTTP_200_OK)


class RoleDetailApi(RoleGetApi, RoleDeleteApi):
    """GET and DELETE share `/roles/<uuid>/`. Method is the action."""

    authorization_actions = {
        "GET": "security:role:get",
        "DELETE": "security:role:delete",
    }
