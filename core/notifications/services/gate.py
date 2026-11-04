from dataclasses import dataclass

from django.conf import settings

from core.notifications.constants import (
    CATEGORIES,
    CHANNELS,
    CHANNEL_EMAIL,
    CHANNEL_IN_APP,
    CHANNEL_PUSH,
    CHANNEL_SMS,
    CHANNEL_TELEGRAM,
    DEFAULT_CHANNEL_ENABLED,
    MANDATORY_CHANNELS_BY_CATEGORY,
)
from core.notifications.models import NotificationPreference
from core.users.models import User


@dataclass(frozen=True, slots=True)
class GateResult:
    skip: bool
    reason: str = ""
    destination: str = ""


def is_mandatory(*, channel: str, category: str) -> bool:
    return channel in MANDATORY_CHANNELS_BY_CATEGORY.get(category, frozenset())


def preference_enabled(*, user: User, channel: str, category: str) -> tuple[bool, str]:
    row = (
        NotificationPreference.objects.filter(
            user=user,
            channel=channel,
            category=category,
            deleted_at__isnull=True,
        )
        .only("enabled", "destination")
        .first()
    )
    if row is None:
        return DEFAULT_CHANNEL_ENABLED.get(channel, False), ""
    return bool(row.enabled), row.destination or ""


def resolve_destination(*, user: User, channel: str, stored: str) -> str:
    if stored:
        return stored
    if channel == CHANNEL_IN_APP:
        return str(user.id)
    if channel == CHANNEL_EMAIL:
        return user.email or ""
    if channel == CHANNEL_SMS:
        return str(user.phone_number) if user.phone_number else ""
    if channel in {CHANNEL_PUSH, CHANNEL_TELEGRAM}:
        return ""
    return ""


def gate_delivery(
    *,
    user: User,
    channel: str,
    category: str,
    senders: dict,
) -> GateResult:
    if not user.is_active:
        return GateResult(skip=True, reason="account inactive")
    if channel not in CHANNELS:
        return GateResult(skip=True, reason="unknown channel")
    if category not in CATEGORIES:
        return GateResult(skip=True, reason="unknown category")
    if channel not in senders:
        return GateResult(skip=True, reason="channel disabled")
    enabled, stored_dest = preference_enabled(user=user, channel=channel, category=category)
    if not enabled and not is_mandatory(channel=channel, category=category):
        return GateResult(skip=True, reason="preference off")
    destination = resolve_destination(user=user, channel=channel, stored=stored_dest)
    if channel != CHANNEL_IN_APP and not destination:
        return GateResult(skip=True, reason="destination missing")
    _ = settings
    return GateResult(skip=False, destination=destination)
