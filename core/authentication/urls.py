from django.urls import path

from .apis import (
    CurrentUserPasswordChangeApi,
    MeApi,
    PasswordResetConfirmApi,
    TokenBlacklistApi,
    TokenObtainPairApi,
    TokenRefreshApi,
    TokenVerifyApi,
)

app_name = "authentication"

urlpatterns = [
    path("me/", MeApi.as_view(), name="me"),
    path("me/password/", CurrentUserPasswordChangeApi.as_view(), name="me_password_change"),
    path("password-reset/confirm/", PasswordResetConfirmApi.as_view(), name="password_reset_confirm"),
    path("token/", TokenObtainPairApi.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshApi.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyApi.as_view(), name="token_verify"),
    path("token/blacklist/", TokenBlacklistApi.as_view(), name="token_blacklist"),
]
