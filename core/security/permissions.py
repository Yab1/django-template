from core.security.registry import register_permission


def register_security_permissions() -> None:
    register_permission(code="security:permission:list", name="List permission catalog")
    register_permission(code="security:permission:get", name="Get permission")
    register_permission(code="security:role:create", name="Create role")
    register_permission(code="security:role:list", name="List roles")
    register_permission(code="security:role:get", name="Get role")
    register_permission(code="security:role:update", name="Update role")
    register_permission(code="security:role:delete", name="Delete role")
    register_permission(code="security:user_role:list", name="List a user's roles")
    register_permission(code="security:user_role:assign", name="Assign a role to a user")
    register_permission(code="security:user_role:revoke", name="Revoke a role from a user")
