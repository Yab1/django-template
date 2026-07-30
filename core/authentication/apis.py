from django.core.exceptions import ValidationError as DjangoValidationError
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from core.api.serializers import build_success_response_serializer
from core.api.views import AuthorizedAPIView
from core.authentication.serializers import (
    CurrentUserPasswordChangeInputSerializer,
    CurrentUserPasswordChangeOutputSerializer,
    CustomTokenBlacklistSerializer,
    CustomTokenObtainPairSerializer,
    MeOutputSerializer,
    PasswordResetConfirmInputSerializer,
    PasswordResetConfirmOutputSerializer,
)
from core.users.services import user_password_change, user_password_reset_from_token


@extend_schema(
    tags=["authentication"],
    description="Obtain access and refresh tokens (username + password).",
    summary="Obtain access and refresh tokens (username + password)",
)
class TokenObtainPairApi(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    tags=["authentication"],
    description="Exchange a refresh token for a new access token.",
    summary="Exchange a refresh token for a new access token",
)
class TokenRefreshApi(TokenRefreshView):
    pass


@extend_schema(
    tags=["authentication"],
    description="Verify that a token is valid.",
    summary="Verify that a token is valid",
)
class TokenVerifyApi(TokenVerifyView):
    pass


@extend_schema(
    tags=["authentication"],
    description="Blacklist a refresh token (logout).",
    summary="Blacklist a refresh token (logout)",
)
class TokenBlacklistApi(TokenBlacklistView):
    serializer_class = CustomTokenBlacklistSerializer


class MeApi(AuthorizedAPIView):
    OutputSerializer = MeOutputSerializer

    # Profile read must remain accessible while must_change_password=True so the
    # frontend can detect the flag and redirect to the set-password page.
    skip_must_change_password_check = True

    SuccessResponseSerializer = build_success_response_serializer(
        component_name="MeSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        tags=["authentication"],
        responses={200: SuccessResponseSerializer},
        description="Return the authenticated user profile.",
        summary="Get authenticated user profile",
    )
    def get(self, request) -> Response:
        return_data = self.OutputSerializer({"user": request.user}).data
        return Response(data=return_data, status=status.HTTP_200_OK)


class CurrentUserPasswordChangeApi(AuthorizedAPIView):
    """Change password for the authenticated user."""

    # Accessible while must_change_password=True: user may change via current password
    # rather than email link. _apply_password_change clears the flag on success.
    skip_must_change_password_check = True

    InputSerializer = CurrentUserPasswordChangeInputSerializer
    OutputSerializer = CurrentUserPasswordChangeOutputSerializer

    SuccessResponseSerializer = build_success_response_serializer(
        component_name="CurrentUserPasswordChangeSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        tags=["authentication"],
        request=InputSerializer,
        responses={200: SuccessResponseSerializer},
        description=(
            "Change the authenticated user's password. Validates Django password policy "
            "(including history) before saving."
        ),
        summary="Change current user password",
    )
    def post(self, request) -> Response:
        ser = self.InputSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        try:
            user_password_change(
                user=request.user,
                current_password=ser.validated_data["current_password"],
                new_password=ser.validated_data["new_password"],
            )
        except DjangoValidationError as exc:
            if hasattr(exc, "error_dict"):
                raise serializers.ValidationError(detail=dict(exc.message_dict)) from exc
            raise serializers.ValidationError(detail=list(exc.messages)) from exc
        out = self.OutputSerializer({"updated": True}).data
        return Response(out, status=status.HTTP_200_OK)


class PasswordResetConfirmApi(APIView):
    """
    Validate a one-time password reset token and set a new password.

    Public endpoint — no authentication required. Token is Django HMAC
    (``default_token_generator``) and single-use: invalidated once the password hash changes.

    On success, ``must_change_password`` is cleared.

    Returns 400 with ``code: invalid_reset_token`` when the uid is malformed,
    the user does not exist, or the token has expired or already been used.
    """

    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]

    InputSerializer = PasswordResetConfirmInputSerializer
    OutputSerializer = PasswordResetConfirmOutputSerializer

    SuccessResponseSerializer = build_success_response_serializer(
        component_name="PasswordResetConfirmSuccessResponse",
        result_serializer=OutputSerializer,
    )

    @extend_schema(
        tags=["authentication"],
        request=InputSerializer,
        responses={200: SuccessResponseSerializer},
        description=(
            "Consume a one-time password reset token and set a new permanent password. "
            "Token is invalidated on first successful use. Clears must_change_password."
        ),
        summary="Confirm password reset via email token",
    )
    def post(self, request) -> Response:
        ser = self.InputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            user_password_reset_from_token(
                uidb64=ser.validated_data["uid"],
                token=ser.validated_data["token"],
                new_password=ser.validated_data["new_password"],
            )
        except DjangoValidationError as exc:
            if hasattr(exc, "error_dict"):
                raise serializers.ValidationError(detail=dict(exc.message_dict)) from exc
            raise serializers.ValidationError(detail=list(exc.messages)) from exc
        out = self.OutputSerializer({"password_set": True}).data
        return Response(out, status=status.HTTP_200_OK)
