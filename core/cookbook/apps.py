from django.apps import AppConfig


class CookbookConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.cookbook"
    verbose_name = "Cookbook"

    def ready(self) -> None:
        from core.cookbook.permissions import register_cookbook_permissions
        from core.cookbook.targets import register_cookbook_file_targets

        register_cookbook_file_targets()
        register_cookbook_permissions()
