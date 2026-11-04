from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.notifications.models import NotificationPreference


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin interface for NotificationPreference model."""

    list_display = ("id", "user", "channel", "category", "enabled", "created_at")
    list_filter = ("channel", "category", "enabled", "created_at")
    search_fields = ("id", "user__email", "user__username", "destination")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("user",)
    ordering = ("-created_at",)
    show_in_index = True
    fieldsets = (
        (_("Basic Information"), {"fields": ("id", "user", "channel", "category")}),
        (_("Preference"), {"fields": ("enabled", "destination")}),
        (_("Visibility"), {"fields": ("is_visible", "deleted_at", "deleted_by")}),
        (_("Metadata"), {"fields": ("created_at", "updated_at", "metadata"), "classes": ("collapse",)}),
    )
