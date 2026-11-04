from core.security.registry import register_permission


def register_notifications_permissions() -> None:
    register_permission(code="notifications:send", name="Send a notification")
    register_permission(code="notifications:delivery:list", name="List notification deliveries")
    register_permission(code="notifications:delivery:get", name="Get a notification delivery")
    register_permission(code="notifications:delivery:retry", name="Retry a notification delivery")
    register_permission(code="notifications:template:list", name="List notification templates")
    register_permission(code="notifications:template:update", name="Update a notification template")
