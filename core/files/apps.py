from django.apps import AppConfig


class FilesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.files"
    verbose_name = "Files"

    def ready(self) -> None:
        from core.files.permissions import register_files_permissions
        from core.files.targets import register_default_targets

        register_default_targets()
        register_files_permissions()
