"""Read-only querysets for users app."""

from typing import Any
from uuid import UUID

from django.db.models import QuerySet
from easyaudit.models import LoginEvent

from core.api.filters import LoginEventFilter
from core.users.authz import authorize, authorize_queryset, authorize_self_or_staff
from core.users.filters import UserFilter
from core.users.models import User

_RESOURCE_USER = "User"


def login_event_list_filters_from_validated(*, validated: dict[str, Any]) -> dict[str, Any]:
    """Map validated login-event list query params to django-filter kwargs."""
    out: dict[str, Any] = {}
    for key in ("login_type", "username", "datetime_from", "datetime_to"):
        if key not in validated:
            continue
        value = validated[key]
        if value is None or value == "":
            continue
        out[key] = value
    return out


def login_event_list(
    *,
    filters: dict | None = None,
    requesting_user: User,
) -> QuerySet[LoginEvent]:
    """All login events (staff/superuser only)."""
    authorize(
        user=requesting_user,
        action="users:user:login_events:list_all",
        resource_code=_RESOURCE_USER,
    )
    filters = filters or {}
    qs = LoginEvent.objects.select_related("user").all()
    return LoginEventFilter(filters, qs).qs.order_by("-datetime", "-id")


def login_event_list_for_user(
    *,
    user_id: UUID,
    requesting_user: User,
    authorization_action: str,
    filters: dict | None = None,
) -> QuerySet[LoginEvent]:
    """Login events for a single user."""
    del authorization_action
    authorize_self_or_staff(user=requesting_user, target_user_id=user_id)
    filters = filters or {}
    qs = LoginEvent.objects.select_related("user").filter(user_id=user_id)
    return LoginEventFilter(filters, qs).qs.order_by("-datetime", "-id")


def user_list(
    *,
    filters: dict | None = None,
    requesting_user: User,
) -> QuerySet[User]:
    """Paginated user directory for staff accounts."""
    filters = dict(filters or {})
    filters.pop("limit", None)
    filters.pop("offset", None)

    base = User.objects.order_by("email")
    qs = authorize_queryset(
        queryset=base,
        user=requesting_user,
        action="users:user:list",
        resource_code=_RESOURCE_USER,
    )
    return UserFilter(filters, qs).qs
