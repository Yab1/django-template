from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from core.notifications.adapters import Outbound, channel_senders, realtime_publish
from core.notifications.constants import (
    CHANNEL_IN_APP,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_SENDING,
    STATUS_SENT,
)
from core.notifications.models import NotificationAttempt, NotificationDelivery
from core.notifications.selectors.inbox import notification_unread_count

logger = logging.getLogger(__name__)


def _backoff_seconds(attempt: int) -> int:
    delays = (60, 600, 3600)
    if attempt <= 1:
        return delays[0]
    if attempt == 2:
        return delays[1]
    return delays[2]


def _delivery_payload(delivery: NotificationDelivery) -> dict:
    return {
        "id": str(delivery.id),
        "reference_id": delivery.reference_id,
        "user_id": str(delivery.user_id),
        "channel": delivery.channel,
        "category": delivery.category,
        "subject": delivery.subject,
        "body": delivery.body,
        "format": delivery.format,
        "status": delivery.status,
        "event_code": delivery.event_code,
        "resource_type": delivery.resource_type,
        "resource_id": str(delivery.resource_id) if delivery.resource_id else None,
        "priority": delivery.priority,
        "read_at": delivery.read_at.isoformat() if delivery.read_at else None,
        "created_at": delivery.created_at.isoformat() if delivery.created_at else None,
    }


def _push_in_app(delivery: NotificationDelivery) -> None:
    if delivery.channel != CHANNEL_IN_APP or delivery.status != STATUS_SENT:
        return
    unread = notification_unread_count(user=delivery.user)
    realtime_publish(
        user_id=delivery.user_id,
        payload={
            "type": "notification",
            "unread_count": unread,
            "delivery": _delivery_payload(delivery),
        },
    )


@transaction.atomic
def notification_dispatch_pending(*, batch_size: int | None = None) -> int:
    """Claim pending rows and send. Runs in the API process after enqueue, and from Celery."""
    if not getattr(settings, "NOTIFICATION_DISPATCH_ENABLED", False):
        return 0
    size = batch_size or int(getattr(settings, "NOTIFICATION_BATCH_SIZE", 25))
    now = timezone.now()
    lock_until = now + timedelta(seconds=30)
    senders = channel_senders()

    rows = list(
        NotificationDelivery.objects.select_for_update(skip_locked=True)
        .filter(
            deleted_at__isnull=True,
            status=STATUS_PENDING,
            next_attempt_at__lte=now,
        )
        .order_by("next_attempt_at", "created_at")[:size]
    )
    if not rows:
        return 0

    for row in rows:
        row.status = STATUS_SENDING
        row.locked_until = lock_until
        row.save(update_fields=["status", "locked_until", "updated_at"])

    processed = 0
    for row in rows:
        processed += 1
        sender = senders.get(row.channel)
        attempt_no = row.attempts + 1
        if sender is None:
            row.status = STATUS_FAILED
            row.last_error = "channel disabled"
            row.attempts = attempt_no
            row.next_attempt_at = None
            row.locked_until = None
            row.save(
                update_fields=["status", "last_error", "attempts", "next_attempt_at", "locked_until", "updated_at"]
            )
            NotificationAttempt.objects.create(
                delivery=row,
                attempt=attempt_no,
                status=STATUS_FAILED,
                error=row.last_error,
            )
            continue
        try:
            provider_ref = sender.send(
                outbound=Outbound(
                    to=row.destination,
                    subject=row.subject,
                    body=row.body,
                    format=row.format,
                ),
            )
            row.status = STATUS_SENT
            row.attempts = attempt_no
            row.last_error = ""
            row.provider_ref = provider_ref or ""
            row.next_attempt_at = None
            row.locked_until = None
            row.save(
                update_fields=[
                    "status",
                    "attempts",
                    "last_error",
                    "provider_ref",
                    "next_attempt_at",
                    "locked_until",
                    "updated_at",
                ],
            )
            NotificationAttempt.objects.create(
                delivery=row,
                attempt=attempt_no,
                status=STATUS_SENT,
            )
            _push_in_app(row)
        except Exception as exc:
            logger.exception("Notification send failed id=%s channel=%s", row.id, row.channel)
            row.attempts = attempt_no
            row.last_error = str(exc)[:2000]
            row.locked_until = None
            if attempt_no >= row.max_attempts:
                row.status = STATUS_FAILED
                row.next_attempt_at = None
            else:
                row.status = STATUS_PENDING
                row.next_attempt_at = timezone.now() + timedelta(seconds=_backoff_seconds(attempt_no))
            row.save(
                update_fields=[
                    "status",
                    "attempts",
                    "last_error",
                    "next_attempt_at",
                    "locked_until",
                    "updated_at",
                ],
            )
            NotificationAttempt.objects.create(
                delivery=row,
                attempt=attempt_no,
                status=STATUS_FAILED,
                error=row.last_error,
            )
    return processed
