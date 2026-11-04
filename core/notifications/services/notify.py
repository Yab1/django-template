from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.notifications.adapters import channel_senders
from core.notifications.constants import (
    CATEGORIES,
    CHANNELS,
    CHANNEL_EMAIL,
    CHANNEL_IN_APP,
    STATUS_PENDING,
    STATUS_SKIPPED,
)
from core.notifications.models import NotificationDelivery
from core.notifications.services.gate import gate_delivery
from core.notifications.services.render import render_template
from core.users.models import User

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def _kick_dispatch() -> None:
    if not getattr(settings, "NOTIFICATION_DISPATCH_ENABLED", False):
        return
    from core.notifications.services.dispatch import notification_dispatch_pending

    notification_dispatch_pending()


@transaction.atomic
def notification_notify(
    *,
    user: User,
    category: str,
    event_code: str,
    data: dict | None = None,
    channels: list[str] | None = None,
    idempotency_key: str | None = None,
    resource_type: str = "",
    resource_id: UUID | None = None,
    priority: str = "normal",
) -> list[NotificationDelivery]:
    """Enqueue one delivery per channel. Dispatch runs after commit when enabled."""
    if category not in CATEGORIES:
        raise ValueError(f"Unknown notification category: {category}")
    payload = dict(data or {})
    key = (idempotency_key or "").strip() or None
    if key and len(key) > 128:
        raise ValueError("idempotency_key must be at most 128 characters")

    if channels is None:
        requested = [CHANNEL_IN_APP, CHANNEL_EMAIL]
    elif not channels:
        requested = list(CHANNELS)
    else:
        requested = list(channels)
    senders = channel_senders()
    max_attempts = int(getattr(settings, "NOTIFICATION_MAX_ATTEMPTS", 5))
    now = timezone.now()
    created: list[NotificationDelivery] = []

    for channel in requested:
        if channel not in CHANNELS:
            raise ValueError(f"Unknown notification channel: {channel}")
        if key:
            existing = NotificationDelivery.objects.filter(
                idempotency_key=key,
                channel=channel,
                deleted_at__isnull=True,
            ).first()
            if existing:
                created.append(existing)
                continue

        gate = gate_delivery(user=user, channel=channel, category=category, senders=senders)
        subject, body, body_format, template = render_template(
            channel=channel,
            category=category,
            data=payload,
        )
        destination = gate.destination or (str(user.id) if channel == CHANNEL_IN_APP else "")
        status = STATUS_SKIPPED if gate.skip else STATUS_PENDING
        row = NotificationDelivery(
            user=user,
            channel=channel,
            category=category,
            template=template,
            destination=destination,
            subject=subject,
            body=body,
            format=body_format,
            status=status,
            max_attempts=max_attempts,
            next_attempt_at=None if gate.skip else now,
            last_error=gate.reason,
            idempotency_key=key,
            event_code=event_code,
            resource_type=resource_type,
            resource_id=resource_id,
            priority=priority,
        )
        row.full_clean()
        row.save()
        created.append(row)

    transaction.on_commit(_kick_dispatch)
    return created
