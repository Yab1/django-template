from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from core.users.models import PasswordHistory, User

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    """Admin interface for User model."""

    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = (
        "id",
        "username",
        "email",
        "phone_number",
        "is_active",
        "is_staff",
        "is_admin",
        "created_at",
    )
    list_filter = (
        "is_active",
        "is_staff",
        "is_admin",
        "is_superuser",
        "must_change_password",
        "is_visible",
        "created_at",
        "updated_at",
    )
    search_fields = ("id", "username", "email", "phone_number")
    readonly_fields = ("id", "created_at", "updated_at", "last_login", "date_joined")
    ordering = ("-created_at",)
    show_in_index = True

    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "id",
                    "username",
                    "email",
                    "phone_number",
                ),
            },
        ),
        (
            _("Status"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_admin",
                    "is_superuser",
                    "must_change_password",
                    "is_visible",
                ),
            },
        ),
        (
            _("Authentication"),
            {
                "fields": ("password",),
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            _("Soft delete"),
            {
                "fields": (
                    "deleted_at",
                    "deleted_by",
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "metadata",
                    "last_login",
                    "date_joined",
                ),
                "classes": ("collapse",),
            },
        ),
    )
    filter_horizontal = ("groups", "user_permissions")


@admin.register(PasswordHistory)
class PasswordHistoryAdmin(ModelAdmin):
    """Admin interface for PasswordHistory model."""

    list_display = ("id", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("id", "user__email", "user__username")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("user",)
    ordering = ("-created_at",)
    show_in_index = True

    fieldsets = (
        (
            _("Password history"),
            {
                "fields": (
                    "id",
                    "user",
                    "hashed_password",
                ),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "metadata",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
