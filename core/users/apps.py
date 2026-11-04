from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.users"

    def ready(self) -> None:
        from core.users.permissions_catalog import register_users_permissions

        register_users_permissions()
