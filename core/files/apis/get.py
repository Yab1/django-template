from uuid import UUID

from django.http import FileResponse, Http404
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response

from core.api.serializers import build_success_response_serializer
from core.api.views import AuthorizedAPIView
from core.files.constants import OPENAPI_TAG_FILES
from core.files.selectors import file_object_get, file_object_visible_to
from core.files.serializers import FileObjectSerializer


def _row_for_user(*, file_id: UUID, user):
    row = file_object_get(file_id=file_id)
    if not file_object_visible_to(row=row, user=user):
        raise Http404("File not found.")
    return row


class FileGetApi(AuthorizedAPIView):
    authorization_resource_code = "File"
    authorization_action = "files:file:get"

    SuccessResponseSerializer = build_success_response_serializer(
        component_name="FileGetSuccessResponse",
        result_serializer=FileObjectSerializer,
    )

    @extend_schema(
        operation_id="files_get",
        tags=[OPENAPI_TAG_FILES],
        responses={200: SuccessResponseSerializer},
        summary="Get file metadata",
    )
    def get(self, request, file_id: UUID) -> Response:
        row = _row_for_user(file_id=file_id, user=request.user)
        return Response(FileObjectSerializer(row, context={"request": request}).data)


class FileDownloadApi(AuthorizedAPIView):
    authorization_resource_code = "File"
    authorization_action = "files:file:download"

    @extend_schema(
        operation_id="files_download",
        tags=[OPENAPI_TAG_FILES],
        responses={200: None},
        summary="Download file bytes",
    )
    def get(self, request, file_id: UUID):
        row = _row_for_user(file_id=file_id, user=request.user)
        handle = row.file.open("rb")
        response = FileResponse(handle, as_attachment=True, filename=row.filename)
        if row.media_type:
            response["Content-Type"] = row.media_type
        return response
