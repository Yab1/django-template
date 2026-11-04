from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response

from core.api.serializers import build_success_response_serializer
from core.api.views import AuthorizedAPIView
from core.files.constants import OPENAPI_TAG_FILES
from core.files.serializers import FileObjectSerializer
from core.files.services import file_object_delete


class FileDeleteApi(AuthorizedAPIView):
    authorization_resource_code = "File"
    authorization_action = "files:file:delete"

    SuccessResponseSerializer = build_success_response_serializer(
        component_name="FileDeleteSuccessResponse",
        result_serializer=FileObjectSerializer,
    )

    @extend_schema(
        operation_id="files_delete",
        tags=[OPENAPI_TAG_FILES],
        responses={200: SuccessResponseSerializer},
        summary="Delete a file",
    )
    def delete(self, request, file_id: UUID) -> Response:
        row = file_object_delete(file_id=file_id, user=request.user)
        return Response(
            FileObjectSerializer(row, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )
