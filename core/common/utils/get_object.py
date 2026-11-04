from typing import Any

from django.http import Http404
from django.shortcuts import get_object_or_404


def get_object(model_or_queryset: Any, **kwargs: Any) -> Any | None:
    """
    Fetch one row by kwargs.

    Wraps ``get_object_or_404`` (supports Model or QuerySet) and returns ``None``
    instead of raising ``Http404`` when missing.
    """
    try:
        return get_object_or_404(model_or_queryset, **kwargs)
    except Http404:
        return None
