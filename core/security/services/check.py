"""
Permission checks.

Full catalog roles live in ``core.security`` when that app lands.
Until then ``PERMISSIONS_ENABLED=False`` (default) allows authenticated callers
through service-level checks; DRF ``PolicyPermission`` still gates tagged APIs
to staff/superuser.
"""

from typing import TypeVar

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from core.users.models import User

_ModelT = TypeVar("_ModelT", bound=QuerySet)

_CACHE_ATTR = "_security_permission_codes"


def user_permission_codes(*, user: User) -> frozenset[str]:
    cached = getattr(user, _CACHE_ATTR, None)
    if cached is not None:
        return cached
    # No permission rows yet — empty set. Superuser / flag short-circuit above.
    codes: frozenset[str] = frozenset()
    setattr(user, _CACHE_ATTR, codes)
    return codes


def clear_user_permission_cache(*, user: User) -> None:
    if hasattr(user, _CACHE_ATTR):
        delattr(user, _CACHE_ATTR)


def user_has_permission(*, user: User, action: str) -> bool:
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    if not getattr(user, "is_active", True):
        return False
    if not getattr(settings, "PERMISSIONS_ENABLED", False):
        return True
    if getattr(user, "is_superuser", False):
        return True
    if not action:
        return False
    return action in user_permission_codes(user=user)


def authorize(
    *,
    user: User,
    action: str,
    resource_code: str | None = None,
    resource_identifier: str | None = None,
) -> None:
    del resource_code, resource_identifier
    if user_has_permission(user=user, action=action):
        return
    raise PermissionDenied(_("You do not have permission to perform this action."))


def authorize_queryset(
    *,
    queryset: _ModelT,
    user: User,
    action: str,
    resource_code: str | None = None,
) -> _ModelT:
    del resource_code
    if user_has_permission(user=user, action=action):
        return queryset
    return queryset.none()
