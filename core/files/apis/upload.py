from typing import Any, cast

from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from core.api.serializers import build_success_response_serializer
from core.api.views import AuthorizedAPIView
from core.files.constants import OPENAPI_TAG_FILES, RESOURCE_ID_DOCUMENT
from core.files.serializers import FileObjectSerializer, FileUploadInputSerializer
from core.files.services import file_object_create


class FileUploadApi(AuthorizedAPIView):
    """Attach a file to a registered resource slot."""

    authorization_resource_code = "File"
    authorization_action = "files:file:upload"

    parser_classes = (MultiPartParser, FormParser)
    InputSerializer = FileUploadInputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="FileUploadSuccessResponse",
        result_serializer=FileObjectSerializer,
    )

    @extend_schema(
        operation_id="files_upload",
        tags=[OPENAPI_TAG_FILES],
        request=InputSerializer,
        responses={201: SuccessResponseSerializer},
        summary="Upload a file",
    )
    def post(self, request) -> Response:
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = cast(dict[str, Any], serializer.validated_data)
        if str(data["resource"]).strip().lower() == RESOURCE_ID_DOCUMENT:
            raise ValidationError({"resource": "Identity documents use the parties document API."})
        row = file_object_create(
            user=request.user,
            upload=data["file"],
            resource=data["resource"],
            field=data["field"],
            object_id=data["object_id"],
        )
        return Response(
            FileObjectSerializer(row, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )
