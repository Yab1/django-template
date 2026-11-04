import django_filters

from core.security.models import Permission, Role


class PermissionFilter(django_filters.FilterSet):
    code = django_filters.CharFilter(field_name="code", lookup_expr="icontains")
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    order_by = django_filters.OrderingFilter(
        fields=[
            ("code", "code"),
            ("name", "name"),
            ("created_at", "created_at"),
        ],
    )

    class Meta:
        model = Permission
        fields = []


class RoleFilter(django_filters.FilterSet):
    code = django_filters.CharFilter(field_name="code", lookup_expr="icontains")
    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    is_visible = django_filters.BooleanFilter(field_name="is_visible", lookup_expr="exact")
    order_by = django_filters.OrderingFilter(
        fields=[
            ("code", "code"),
            ("name", "name"),
            ("created_at", "created_at"),
        ],
    )

    class Meta:
        model = Role
        fields = []
