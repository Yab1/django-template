import django_filters

from core.users.models import User


class UserFilter(django_filters.FilterSet):
    is_visible = django_filters.BooleanFilter(field_name="is_visible", lookup_expr="exact")
    is_deleted = django_filters.BooleanFilter(field_name="deleted_at", lookup_expr="isnull", exclude=True)
    email = django_filters.CharFilter(field_name="email", lookup_expr="icontains")
    order_by = django_filters.OrderingFilter(
        fields=[
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
            ("deleted_at", "deleted_at"),
            ("email", "email"),
        ],
    )

    class Meta:
        model = User
        fields = []
