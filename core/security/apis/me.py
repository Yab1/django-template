from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response

from core.api.serializers import build_success_response_serializer
from core.api.views import AuthorizedAPIView
from core.security.constants import OPENAPI_TAG_SECURITY
from core.security.models import Permission
from core.security.selectors import user_role_list
from core.security.serializers import MePermissionsOutputSerializer, UserRoleOutputSerializer
from core.security.services import ensure_permissions_synced, user_permission_codes


class MePermissionsApi(AuthorizedAPIView):
    """Current user's effective permission codes. Any authenticated user."""

    OutputSerializer = MePermissionsOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="MePermissionsSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="security_me_permissions",
        tags=[OPENAPI_TAG_SECURITY],
        responses={200: SuccessResponseSerializer},
        summary="My permission codes",
    )
    def get(self, request) -> Response:
        roles = list(user_role_list(user_id=request.user.id).values_list("role__code", flat=True))
        if request.user.is_superuser:
            ensure_permissions_synced()
            codes = list(Permission.objects.order_by("code").values_list("code", flat=True))
        else:
            codes = sorted(user_permission_codes(user=request.user))
        payload = {
            "codes": codes,
            "roles": roles,
            "is_superuser": request.user.is_superuser,
        }
        return Response(self.OutputSerializer(payload).data, status=status.HTTP_200_OK)


class MeRolesApi(AuthorizedAPIView):
    """Current user's assigned roles. Any authenticated user."""

    OutputSerializer = UserRoleOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="MeRolesSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="security_me_roles",
        tags=[OPENAPI_TAG_SECURITY],
        responses={200: SuccessResponseSerializer},
        summary="My roles",
    )
    def get(self, request) -> Response:
        qs = user_role_list(user_id=request.user.id)
        return Response(self.OutputSerializer(qs, many=True).data, status=status.HTTP_200_OK)
