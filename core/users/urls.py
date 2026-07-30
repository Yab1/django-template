from django.urls import path

from core.users.apis import (
    CurrentUserLoginEventListApi,
    LoginEventListApi,
    UserListApi,
    UserLoginEventListApi,
    UserPasswordResetApi,
    UserUpdateApi,
)

app_name = "users"

urlpatterns = [
    path("users/", UserListApi.as_view(), name="user-list"),
    path("users/<uuid:id>/password/", UserPasswordResetApi.as_view(), name="user-password-reset"),
    path("users/<uuid:id>/update/", UserUpdateApi.as_view(), name="user-update"),
    path("users/login-events/", LoginEventListApi.as_view(), name="login-event-list"),
    path("users/me/login-events/", CurrentUserLoginEventListApi.as_view(), name="current-user-login-event-list"),
    path("users/<uuid:id>/login-events/", UserLoginEventListApi.as_view(), name="user-login-event-list"),
]
