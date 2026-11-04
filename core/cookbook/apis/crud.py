from typing import Any, cast
from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response

from core.api.pagination import LimitOffsetPagination, get_paginated_response
from core.api.serializers import build_paginated_result_serializer, build_success_response_serializer
from core.api.utils import cache_api_response
from core.api.views import AuthorizedAPIView
from core.cookbook.constants import OPENAPI_TAG_COOKBOOK
from core.cookbook.selectors import recipe_get, recipe_list
from core.cookbook.serializers import (
    RecipeCreateInputSerializer,
    RecipeListQuerySerializer,
    RecipeOutputSerializer,
    RecipeUpdateInputSerializer,
)
from core.cookbook.services import recipe_create, recipe_delete, recipe_update


class RecipeCreateApi(AuthorizedAPIView):
    """Create a draft recipe owned by the caller."""

    authorization_resource_code = "Recipe"
    authorization_action = "cookbook:recipe:create"

    InputSerializer = RecipeCreateInputSerializer
    OutputSerializer = RecipeOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="RecipeCreateSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="cookbook_recipe_create",
        tags=[OPENAPI_TAG_COOKBOOK],
        request=InputSerializer,
        responses={201: SuccessResponseSerializer},
        summary="Create recipe",
    )
    def post(self, request) -> Response:
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)
        obj = recipe_create(
            title=data["title"],
            body=data.get("body", ""),
            created_by=request.user,
        )
        return Response(self.OutputSerializer(obj).data, status=status.HTTP_201_CREATED)


class RecipeListApi(AuthorizedAPIView):
    """Paginated list of recipes the caller may see."""

    authorization_resource_code = "Recipe"
    authorization_action = "cookbook:recipe:list"

    class Pagination(LimitOffsetPagination):
        default_limit = 25
        max_limit = 100

    QuerySerializer = RecipeListQuerySerializer
    PaginatedResultSerializer = build_paginated_result_serializer(
        component_name="RecipeListPaginatedResult",
        item_serializer=RecipeOutputSerializer,
    )
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="RecipeListSuccessResponse",
        result_serializer=PaginatedResultSerializer,
    )

    @extend_schema(
        operation_id="cookbook_recipe_list",
        tags=[OPENAPI_TAG_COOKBOOK],
        parameters=[QuerySerializer],
        responses={200: SuccessResponseSerializer},
        summary="List recipes",
    )
    @cache_api_response(namespace="cookbook:recipe:list")
    def get(self, request) -> Response:
        query_serializer = self.QuerySerializer(data=request.query_params.dict())
        query_serializer.is_valid(raise_exception=True)
        queryset = recipe_list(
            filters=cast(dict[str, Any], query_serializer.validated_data),
            requesting_user=request.user,
        )
        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=RecipeOutputSerializer,
            queryset=queryset,
            request=request,
            view=self,
        )


class RecipeGetApi(AuthorizedAPIView):
    """Fetch one recipe the caller may see."""

    authorization_resource_code = "Recipe"
    authorization_action = "cookbook:recipe:get"

    OutputSerializer = RecipeOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="RecipeGetSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="cookbook_recipe_get",
        tags=[OPENAPI_TAG_COOKBOOK],
        responses={200: SuccessResponseSerializer},
        summary="Get recipe",
    )
    def get(self, request, id: UUID) -> Response:
        obj = recipe_get(recipe_id=id, requesting_user=request.user)
        return Response(self.OutputSerializer(obj).data, status=status.HTTP_200_OK)


class RecipeUpdateApi(AuthorizedAPIView):
    """Patch recipe fields. Status changes go through publish."""

    authorization_resource_code = "Recipe"
    authorization_action = "cookbook:recipe:update"

    InputSerializer = RecipeUpdateInputSerializer
    OutputSerializer = RecipeOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="RecipeUpdateSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="cookbook_recipe_update",
        tags=[OPENAPI_TAG_COOKBOOK],
        request=InputSerializer,
        responses={200: SuccessResponseSerializer},
        summary="Update recipe",
    )
    def patch(self, request, id: UUID) -> Response:
        serializer = self.InputSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        obj = recipe_update(
            recipe_id=id,
            data=cast(dict[str, Any], serializer.validated_data),
            requesting_user=request.user,
        )
        return Response(self.OutputSerializer(obj).data, status=status.HTTP_200_OK)


class RecipeDeleteApi(AuthorizedAPIView):
    """Soft-delete a recipe."""

    authorization_resource_code = "Recipe"
    authorization_action = "cookbook:recipe:delete"

    OutputSerializer = RecipeOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="RecipeDeleteSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="cookbook_recipe_delete",
        tags=[OPENAPI_TAG_COOKBOOK],
        responses={200: SuccessResponseSerializer},
        summary="Delete recipe",
    )
    def delete(self, request, id: UUID) -> Response:
        obj = recipe_delete(recipe_id=id, requesting_user=request.user)
        return Response(self.OutputSerializer(obj).data, status=status.HTTP_200_OK)


class RecipeDetailApi(RecipeGetApi, RecipeDeleteApi):
    """GET and DELETE share `/recipes/<uuid>/`. Method is the action."""

    authorization_actions = {
        "GET": "cookbook:recipe:get",
        "DELETE": "cookbook:recipe:delete",
    }
