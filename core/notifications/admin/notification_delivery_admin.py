from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from core.notifications.models import NotificationAttempt, NotificationDelivery


class NotificationAttemptInline(admin.TabularInline):
    """Inline admin for NotificationAttempt within NotificationDelivery."""

    model = NotificationAttempt
    extra = 0
    min_num = 0
    fields = ("attempt", "status", "error", "created_at")
    readonly_fields = ("attempt", "status", "error", "created_at")
    verbose_name = _("Attempt")
    verbose_name_plural = _("Attempts")


@admin.register(NotificationDelivery)
class NotificationDeliveryAdmin(admin.ModelAdmin):
    """Admin interface for NotificationDelivery model."""

    list_display = ("id", "reference_id", "user", "channel", "category", "status", "created_at")
    list_filter = ("channel", "category", "status", "priority", "created_at")
    search_fields = ("id", "reference_id", "user__email", "subject", "event_code")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("user", "template", "deleted_by")
    ordering = ("-created_at",)
    show_in_index = True
    inlines = (NotificationAttemptInline,)
    fieldsets = (
        (_("Basic Information"), {"fields": ("id", "reference_id", "user", "channel", "category", "template")}),
        (_("Content"), {"fields": ("destination", "subject", "body", "format")}),
        (
            _("Status"),
            {"fields": ("status", "attempts", "max_attempts", "next_attempt_at", "last_error", "provider_ref")},
        ),
        (
            _("Context"),
            {"fields": ("event_code", "resource_type", "resource_id", "priority", "idempotency_key", "read_at")},
        ),
        (_("Visibility"), {"fields": ("is_visible", "deleted_at", "deleted_by")}),
        (_("Metadata"), {"fields": ("created_at", "updated_at", "metadata"), "classes": ("collapse",)}),
    )
