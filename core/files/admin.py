from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.files.models import FileObject


@admin.register(FileObject)
class FileObjectAdmin(admin.ModelAdmin):
    """Admin interface for uploaded files."""

    list_display = (
        "id",
        "reference_id",
        "filename",
        "resource",
        "field",
        "object_id",
        "media_type",
        "created_at",
    )
    list_filter = ("resource", "field", "media_type", "driver", "is_visible", "created_at")
    search_fields = ("id", "reference_id", "filename", "object_id", "resource", "field")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("created_by", "deleted_by")
    ordering = ("-created_at",)
    show_in_index = True
    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("id", "reference_id", "file", "filename")},
        ),
        (
            _("Attachment"),
            {"fields": ("resource", "field", "content_type", "object_id")},
        ),
        (
            _("Storage"),
            {"fields": ("media_type", "size", "driver", "created_by")},
        ),
        (
            _("Visibility"),
            {"fields": ("is_visible", "deleted_at", "deleted_by")},
        ),
        (
            _("Metadata"),
            {"fields": ("created_at", "updated_at", "metadata"), "classes": ("collapse",)},
        ),
    )
