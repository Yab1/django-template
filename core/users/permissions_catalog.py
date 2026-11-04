from core.security.registry import register_permission


def register_users_permissions() -> None:
    register_permission(code="users:user:list", name="List users")
    register_permission(code="users:user:update", name="Update user")
    register_permission(code="users:user:password_reset", name="Reset another user's password")
