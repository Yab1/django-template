from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response

from core.api.serializers import build_success_response_serializer
from core.api.views import AuthorizedAPIView
from core.security.constants import OPENAPI_TAG_SECURITY
from core.security.selectors import user_role_list
from core.security.serializers import UserRoleAssignInputSerializer, UserRoleOutputSerializer
from core.security.services import user_role_assign_by_ids, user_role_revoke


class UserRoleListApi(AuthorizedAPIView):
    authorization_resource_code = "UserRole"
    authorization_action = "security:user_role:list"

    OutputSerializer = UserRoleOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="UserRoleListSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="security_user_role_list",
        tags=[OPENAPI_TAG_SECURITY],
        responses={200: SuccessResponseSerializer},
        summary="List a user's roles",
    )
    def get(self, request, user_id: UUID) -> Response:
        qs = user_role_list(user_id=user_id)
        return Response(self.OutputSerializer(qs, many=True).data, status=status.HTTP_200_OK)


class UserRoleAssignApi(AuthorizedAPIView):
    authorization_resource_code = "UserRole"
    authorization_action = "security:user_role:assign"

    InputSerializer = UserRoleAssignInputSerializer
    OutputSerializer = UserRoleOutputSerializer
    SuccessResponseSerializer = build_success_response_serializer(
        component_name="UserRoleAssignSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        operation_id="security_user_role_assign",
        tags=[OPENAPI_TAG_SECURITY],
        request=InputSerializer,
        responses={201: SuccessResponseSerializer},
        summary="Assign a role to a user",
    )
    def post(self, request, user_id: UUID) -> Response:
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        link = user_role_assign_by_ids(
            user_id=user_id,
            role_id=serializer.validated_data["role_id"],
            assigned_by=request.user,
        )
        link = user_role_list(user_id=user_id).get(pk=link.id)
        return Response(self.OutputSerializer(link).data, status=status.HTTP_201_CREATED)


class UserRoleRevokeApi(AuthorizedAPIView):
    authorization_resource_code = "UserRole"
    authorization_action = "security:user_role:revoke"

    @extend_schema(
        operation_id="security_user_role_revoke",
        tags=[OPENAPI_TAG_SECURITY],
        responses={200: None},
        summary="Revoke a role from a user",
    )
    def post(self, request, user_id: UUID, role_id: UUID) -> Response:
        user_role_revoke(user_id=user_id, role_id=role_id)
        return Response({"revoked": True}, status=status.HTTP_200_OK)
