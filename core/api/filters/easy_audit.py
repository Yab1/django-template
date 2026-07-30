"""
django-filter sets and query validation for django-easy-audit ``CRUDEvent`` lists.

Use on any resource that exposes easy-audit CRUD lists: base queryset must already
scope ``content_type`` / ``object_id``; these filters only narrow by event metadata.
"""

from typing import Any

import django_filters
from django import forms
from easyaudit.models import CRUDEvent
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request

from core.common.enums import CrudEventType, crud_event_type_to_int


class CrudEventFilter(django_filters.FilterSet):
    event_type = django_filters.NumberFilter()
    user_id = django_filters.UUIDFilter()
    datetime_from = django_filters.DateTimeFilter(field_name="datetime", lookup_expr="gte")
    datetime_to = django_filters.DateTimeFilter(field_name="datetime", lookup_expr="lte")

    class Meta:
        model = CRUDEvent
        fields = []


class CrudEventAuditListQueryForm(forms.Form):
    """
    Validates query params for ``CrudEventFilter`` on any easy-audit list endpoint.

    API uses ``CrudEventType`` strings; after validation ``event_type`` is the easy-audit
    **integer** so the dict can be passed straight into ``FilterSet`` / selectors.
    """

    event_type = forms.ChoiceField(choices=CrudEventType.choices, required=False)
    user_id = forms.UUIDField(required=False)
    datetime_from = forms.DateTimeField(required=False)
    datetime_to = forms.DateTimeField(required=False)

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        if cleaned_data is None:
            return {}
        et = cleaned_data.get("event_type")
        # ChoiceField may bind ``event_type=`` as ``''``; treat like “not provided”.
        if et in (None, ""):
            cleaned_data["event_type"] = None
        else:
            cleaned_data["event_type"] = crud_event_type_to_int(et)
        return cleaned_data


def get_crud_event_audit_filters(request: Request) -> dict[str, Any]:
    """
    Parse and validate ``event_type`` / ``user_id`` / ``datetime_*`` from the request.

    Uses ``query_params`` (DRF) / ``GET`` (Django).
    """
    form = CrudEventAuditListQueryForm(request.query_params)
    if not form.is_valid():
        raise ValidationError(form.errors)
    return {k: v for k, v in form.cleaned_data.items() if v is not None and v != ""}
