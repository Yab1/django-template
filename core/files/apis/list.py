from typing import Any, cast

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response

from core.api.pagination import LimitOffsetPagination, get_paginated_response
from core.api.serializers import build_paginated_result_serializer, build_success_response_serializer
from core.api.views import AuthorizedAPIView
from core.files.constants import OPENAPI_TAG_FILES
from core.files.selectors import file_object_list
from core.files.serializers import FileListQuerySerializer, FileObjectSerializer


class FileListApi(AuthorizedAPIView):
    """List files for a resource + object_id."""

    authorization_resource_code = "File"
    authorization_action = "files:file:list"

    class Pagination(LimitOffsetPagination):
        default_limit = 25
        max_limit = 100

    QuerySerializer = FileListQuerySerializer
    PaginatedResultSerializer = build_paginated_result_serializer(
        component_name="FileListPaginatedResult",
        item_serializer=FileObjectSerializer,
    )
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="FileListSuccessResponse",
        result_serializer=PaginatedResultSerializer,
    )

    @extend_schema(
        operation_id="files_list",
        tags=[OPENAPI_TAG_FILES],
        parameters=[QuerySerializer],
        responses={200: SuccessResponseSerializer},
        summary="List files",
    )
    def get(self, request) -> Response:
        query = self.QuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        data = cast(dict[str, Any], query.validated_data)
        queryset = file_object_list(
            user=request.user,
            resource=data["resource"],
            object_id=data["object_id"],
            field=data.get("field") or None,
        )
        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=FileObjectSerializer,
            queryset=queryset,
            request=request,
            view=self,
        )
