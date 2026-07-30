"""Authentication-related side effects (django-easy-audit ``LoginEvent`` rows)."""

from django.db import transaction
from django.http import HttpRequest
from easyaudit.models import LoginEvent
from easyaudit.settings import DATABASE_ALIAS, REMOTE_ADDR_HEADER

from core.users.models import User


def _remote_ip(*, request: HttpRequest | None) -> str:
    if request is None:
        return ""
    return (request.META.get(REMOTE_ADDR_HEADER) or "")[:50]


def login_event_failed_record(*, username: str, request: HttpRequest | None) -> None:
    """
    Persist a ``LoginEvent`` row for a failed credential check (JWT obtain path).

    django-easy-audit's ``user_login_failed`` handler reads ``get_current_request()`` only;
    that can miss API requests, so JWT failures are recorded here explicitly.
    """
    with transaction.atomic(using=DATABASE_ALIAS):
        LoginEvent.objects.using(DATABASE_ALIAS).create(
            login_type=LoginEvent.FAILED,
            username=(username or "")[:255],
            user=None,
            remote_ip=_remote_ip(request=request),
        )


def login_event_logout_record(*, user: User, request: HttpRequest | None) -> None:
    """
    Persist a ``LoginEvent`` row when a refresh token is blacklisted (API logout).

    SimpleJWT's blacklist view does not call ``django.contrib.auth.logout()`` or emit
    ``user_logged_out``, so easy-audit never sees a logout for token-based sessions.
    """
    with transaction.atomic(using=DATABASE_ALIAS):
        LoginEvent.objects.using(DATABASE_ALIAS).create(
            login_type=LoginEvent.LOGOUT,
            username=getattr(user, user.USERNAME_FIELD)[:255],
            user=user,
            remote_ip=_remote_ip(request=request),
        )
