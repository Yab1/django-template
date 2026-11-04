from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.notifications.models import NotificationTemplate


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Admin interface for NotificationTemplate model."""

    list_display = ("id", "reference_id", "channel", "category", "locale", "is_active", "created_at")
    list_filter = ("channel", "category", "is_active", "created_at")
    search_fields = ("id", "reference_id", "subject", "body")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("channel", "category")
    show_in_index = True
    fieldsets = (
        (_("Basic Information"), {"fields": ("id", "reference_id", "channel", "category", "locale")}),
        (_("Content"), {"fields": ("subject", "body", "format", "is_active")}),
        (_("Visibility"), {"fields": ("is_visible", "deleted_at", "deleted_by")}),
        (_("Metadata"), {"fields": ("created_at", "updated_at", "metadata"), "classes": ("collapse",)}),
    )
