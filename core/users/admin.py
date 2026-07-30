from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import User
from .services import user_create

# Unregister default admin classes
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    # Forms loaded from `unfold.forms`
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    base_model = User
    list_display: list[str] = [
        "email",
        "full_name",
        "is_staff",
        "is_active",
    ]
    list_filter: list[str] = [
        "is_staff",
        "is_superuser",
        "is_active",
        "groups",
    ]
    search_fields: list[str] = ["email", "first_name", "last_name"]
    ordering: list[str] = ["email"]
    fieldsets = (
        (
            "Authentication Info",
            {
                "fields": (
                    "email",
                    "password",
                ),
            },
        ),
        (
            "Personal Info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone_number",
                ),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important Dates",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                    "updated_at",
                ),
            },
        ),
    )

    readonly_fields: list[str] = [
        "last_login",
        "date_joined",
        "updated_at",
    ]
    filter_horizontal: list[str] = [
        "groups",
        "user_permissions",
    ]
    show_in_index = True

    def save_model(self, request, obj, form, change):
        if change:
            return super().save_model(request, obj, form, change)

        try:
            user_create(**form.cleaned_data)
        except ValidationError as exc:
            self.message_user(request, str(exc), messages.ERROR)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
