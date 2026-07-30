from typing import Any, cast
from uuid import UUID

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response

from core.api.pagination import LimitOffsetPagination, get_paginated_response
from core.api.serializers import (
    LoginEventListQuerySerializer,
    LoginEventOutputSerializer,
    build_paginated_result_serializer,
    build_success_response_serializer,
)
from core.api.views import AuthorizedAPIView
from core.users.constants import OPENAPI_TAG_USERS
from core.users.models import User
from core.users.selectors import (
    login_event_list,
    login_event_list_filters_from_validated,
    login_event_list_for_user,
)


class LoginEventListApi(AuthorizedAPIView):
    """Global login-event stream; super/admin policy bundle only."""

    authorization_resource_code = "User"
    authorization_action = "users:user:login_events:list_all"

    class Pagination(LimitOffsetPagination):
        default_limit = 20
        max_limit = 100

    PaginatedResultSerializer = build_paginated_result_serializer(
        component_name="UserLoginEventListAllPaginatedResult",
        item_serializer=LoginEventOutputSerializer,
    )
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="UserLoginEventListAllSuccessResponse",
        result_serializer=PaginatedResultSerializer,
    )

    @extend_schema(
        operation_id="users_login_events_list_all",
        tags=[OPENAPI_TAG_USERS],
        parameters=[LoginEventListQuerySerializer],
        responses={200: SuccessResponseSerializer},
        description="Paginated list of login events across all users.",
        summary="List all login events",
    )
    def get(self, request) -> Response:
        query_serializer = LoginEventListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated = cast(dict[str, Any], query_serializer.validated_data)
        filters = login_event_list_filters_from_validated(validated=validated)
        queryset = login_event_list(filters=filters, requesting_user=request.user)
        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=LoginEventOutputSerializer,
            queryset=queryset,
            request=request,
            view=self,
        )


class CurrentUserLoginEventListApi(AuthorizedAPIView):
    """Own login history; policy ``users:user:login_events:list_me`` on ``User``."""

    authorization_resource_code = "User"
    authorization_action = "users:user:login_events:list_me"

    class Pagination(LimitOffsetPagination):
        default_limit = 20
        max_limit = 100

    PaginatedResultSerializer = build_paginated_result_serializer(
        component_name="UserMeLoginEventListPaginatedResult",
        item_serializer=LoginEventOutputSerializer,
    )
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="UserMeLoginEventListSuccessResponse",
        result_serializer=PaginatedResultSerializer,
    )

    @extend_schema(
        operation_id="users_me_login_events_list",
        tags=[OPENAPI_TAG_USERS],
        parameters=[LoginEventListQuerySerializer],
        responses={200: SuccessResponseSerializer},
        description="Paginated login events for the authenticated user.",
        summary="List login events for the current user",
    )
    def get(self, request) -> Response:
        query_serializer = LoginEventListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated = cast(dict[str, Any], query_serializer.validated_data)
        filters = login_event_list_filters_from_validated(validated=validated)
        queryset = login_event_list_for_user(
            user_id=request.user.id,
            requesting_user=request.user,
            authorization_action="users:user:login_events:list_me",
            filters=filters,
        )
        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=LoginEventOutputSerializer,
            queryset=queryset,
            request=request,
            view=self,
        )


class UserLoginEventListApi(AuthorizedAPIView):
    """Paginated login events for a single user account."""

    authorization_resource_code = "User"
    authorization_action = "users:user:login_events:list"

    class Pagination(LimitOffsetPagination):
        default_limit = 20
        max_limit = 100

    PaginatedResultSerializer = build_paginated_result_serializer(
        component_name="UserLoginEventListByUserIdPaginatedResult",
        item_serializer=LoginEventOutputSerializer,
    )
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="UserLoginEventListByUserIdSuccessResponse",
        result_serializer=PaginatedResultSerializer,
    )

    @extend_schema(
        operation_id="users_user_login_events_list",
        tags=[OPENAPI_TAG_USERS],
        parameters=[LoginEventListQuerySerializer],
        responses={200: SuccessResponseSerializer},
        description="Paginated login events for a specific user.",
        summary="List login events for a user",
    )
    def get(self, request, id: UUID) -> Response:
        get_object_or_404(User, pk=id)
        query_serializer = LoginEventListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        validated = cast(dict[str, Any], query_serializer.validated_data)
        filters = login_event_list_filters_from_validated(validated=validated)
        queryset = login_event_list_for_user(
            user_id=id,
            requesting_user=request.user,
            authorization_action="users:user:login_events:list",
            filters=filters,
        )
        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=LoginEventOutputSerializer,
            queryset=queryset,
            request=request,
            view=self,
        )
