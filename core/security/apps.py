from django.apps import AppConfig


class SecurityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.security"
    verbose_name = "Security"

    def ready(self) -> None:
        from django.db.models.signals import post_migrate

        from core.security.permissions import register_security_permissions

        register_security_permissions()
        post_migrate.connect(_sync_permissions, sender=self)


def _sync_permissions(sender, **kwargs) -> None:
    from core.security.services.permission import permission_sync_from_registry

    permission_sync_from_registry()
