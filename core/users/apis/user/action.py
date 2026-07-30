from uuid import UUID

from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response

from core.api.serializers import build_success_response_serializer
from core.api.views import AuthorizedAPIView
from core.users.constants import OPENAPI_TAG_USERS
from core.users.models import User
from core.users.serializers import UserPasswordResetInputSerializer, UserPasswordResetOutputSerializer
from core.users.services import user_password_reset


class UserPasswordResetApi(AuthorizedAPIView):
    """Set another user's password when policy allows (``users:user:password_reset``)."""

    authorization_resource_code = "User"
    authorization_action = "users:user:password_reset"

    InputSerializer = UserPasswordResetInputSerializer
    OutputSerializer = UserPasswordResetOutputSerializer

    SuccessResponseSerializer = build_success_response_serializer(
        component_name="UserPasswordResetSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        tags=[OPENAPI_TAG_USERS],
        request=InputSerializer,
        responses={200: SuccessResponseSerializer},
        description=(
            "Set another user's new password. "
            "Archives the previous encoded password for history (reuse rules still apply)."
        ),
        summary="Reset user password",
    )
    def post(self, request, id: UUID) -> Response:

        target = User.objects.get(pk=id)
        ser = self.InputSerializer(
            data=request.data,
            context={"request": request, "target_user": target},
        )
        ser.is_valid(raise_exception=True)

        try:
            user_password_reset(
                target_user=target,
                new_password=ser.validated_data["new_password"],
                requesting_user=request.user,
            )
        except DjangoValidationError as exc:
            if hasattr(exc, "error_dict"):
                raise serializers.ValidationError(detail=dict(exc.message_dict)) from exc
            raise serializers.ValidationError(detail=list(exc.messages)) from exc

        out = self.OutputSerializer({"updated": True}).data
        return Response(out, status=status.HTTP_200_OK)
