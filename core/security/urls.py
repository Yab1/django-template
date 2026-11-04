from django.urls import path

from core.security.apis import (
    MePermissionsApi,
    MeRolesApi,
    PermissionGetApi,
    PermissionListApi,
    RoleCreateApi,
    RoleDetailApi,
    RoleListApi,
    RoleUpdateApi,
    UserRoleAssignApi,
    UserRoleListApi,
    UserRoleRevokeApi,
)

app_name = "security"

urlpatterns = [
    path("security/me/permissions/", MePermissionsApi.as_view(), name="me-permissions"),
    path("security/me/roles/", MeRolesApi.as_view(), name="me-roles"),
    path("security/permissions/", PermissionListApi.as_view(), name="permission-list"),
    path("security/permissions/<uuid:id>/", PermissionGetApi.as_view(), name="permission-get"),
    path("security/roles/", RoleListApi.as_view(), name="role-list"),
    path("security/roles/create/", RoleCreateApi.as_view(), name="role-create"),
    path("security/roles/<uuid:id>/", RoleDetailApi.as_view(), name="role-detail"),
    path("security/roles/<uuid:id>/update/", RoleUpdateApi.as_view(), name="role-update"),
    path("security/users/<uuid:user_id>/roles/", UserRoleListApi.as_view(), name="user-role-list"),
    path(
        "security/users/<uuid:user_id>/roles/assign/",
        UserRoleAssignApi.as_view(),
        name="user-role-assign",
    ),
    path(
        "security/users/<uuid:user_id>/roles/<uuid:role_id>/revoke/",
        UserRoleRevokeApi.as_view(),
        name="user-role-revoke",
    ),
]
