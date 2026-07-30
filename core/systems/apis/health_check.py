from dataclasses import asdict

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.renderers import DEFAULT_META, DEFAULT_SUCCESS_MESSAGE
from core.api.serializers import build_error_response_serializer, build_success_response_serializer
from core.systems.constants import OPENAPI_TAG_SYSTEMS
from core.systems.selectors import system_health_get
from core.systems.serializers import SystemHealthCheckOutputSerializer


class SystemHealthCheckApi(APIView):
    permission_classes = [AllowAny]

    OutputSerializer = SystemHealthCheckOutputSerializer

    SuccessResponseSerializer = build_success_response_serializer(
        component_name="SystemHealthCheckSuccessResponse",
        result_serializer=OutputSerializer,
    )
    ErrorResponseSerializer = build_error_response_serializer(
        component_name="SystemHealthCheckErrorResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        tags=[OPENAPI_TAG_SYSTEMS],
        request=None,
        responses={200: SuccessResponseSerializer, 503: ErrorResponseSerializer},
        description=(
            "Check database, cache, RabbitMQ (Celery broker), and MinIO (when MinIO is the default file "
            "storage) connectivity. Returns 503 when any probed component is ``error``. ``rabbitmq`` is "
            "``not_configured`` when ``CELERY_BROKER_URL`` is unset or Celery eager mode is on (does not fail health). "
            "``minio`` is ``not_configured`` when the default storage backend is not MinIO (does not fail health). "
            "When MinIO is used, a missing media bucket is created if ``MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET`` is "
            "true; otherwise a missing bucket still reports ``ok``. Response uses the standard API envelope "
            "(``result`` holds probe fields including ``status`` ok/unhealthy)."
        ),
        summary="System health check",
    )
    def get(self, request) -> Response:
        result = system_health_get()
        inner = self.OutputSerializer(asdict(result)).data
        if result.status == "ok":
            body = {
                "status": "success",
                "result": inner,
                "meta": DEFAULT_META,
                "message": DEFAULT_SUCCESS_MESSAGE,
            }
            return Response(data=body, status=status.HTTP_200_OK)
        body = {
            "status": "error",
            "result": inner,
            "meta": DEFAULT_META,
            "message": "One or more system dependencies are unhealthy.",
        }
        return Response(data=body, status=status.HTTP_503_SERVICE_UNAVAILABLE)
