"""Staff-based authorization helpers until the security app is wired in."""

from typing import TypeVar

from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from core.users.models import User

_ModelT = TypeVar("_ModelT", bound=QuerySet)


def authorize(
    *,
    user: User,
    action: str,
    resource_code: str,
    resource_identifier: str | None = None,
) -> None:
    del action, resource_code, resource_identifier
    if user.is_staff or user.is_superuser:
        return
    raise PermissionDenied(_("You do not have permission to perform this action."))


def authorize_self_or_staff(*, user: User, target_user_id) -> None:
    if user.pk == target_user_id:
        return
    if user.is_staff or user.is_superuser:
        return
    raise PermissionDenied(_("You do not have permission to perform this action."))


def authorize_queryset(
    *,
    queryset: _ModelT,
    user: User,
    action: str,
    resource_code: str,
) -> _ModelT:
    del action, resource_code
    if user.is_staff or user.is_superuser:
        return queryset
    return queryset.none()
