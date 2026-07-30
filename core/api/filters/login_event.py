"""django-filter sets for django-easy-audit ``LoginEvent`` lists."""

import django_filters
from easyaudit.models import LoginEvent


class LoginEventFilter(django_filters.FilterSet):
    login_type = django_filters.NumberFilter()
    username = django_filters.CharFilter(lookup_expr="icontains")
    datetime_from = django_filters.DateTimeFilter(field_name="datetime", lookup_expr="gte")
    datetime_to = django_filters.DateTimeFilter(field_name="datetime", lookup_expr="lte")

    class Meta:
        model = LoginEvent
        fields = []
