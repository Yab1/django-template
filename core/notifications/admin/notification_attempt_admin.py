from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.notifications.models import NotificationAttempt


@admin.register(NotificationAttempt)
class NotificationAttemptAdmin(admin.ModelAdmin):
    """Admin interface for NotificationAttempt model."""

    list_display = ("id", "delivery", "attempt", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "delivery__reference_id", "error")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("delivery",)
    ordering = ("-created_at",)
    show_in_index = True
    fieldsets = (
        (_("Attempt"), {"fields": ("id", "delivery", "attempt", "status", "error")}),
        (_("Metadata"), {"fields": ("created_at", "updated_at", "metadata"), "classes": ("collapse",)}),
    )
