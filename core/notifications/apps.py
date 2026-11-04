from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.notifications"
    verbose_name = "Notifications"

    def ready(self) -> None:
        from core.notifications.permissions import register_notifications_permissions

        register_notifications_permissions()
