from uuid import UUID

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core.notifications.adapters import realtime_publish
from core.notifications.constants import CHANNEL_IN_APP, STATUS_SENT
from core.notifications.models import NotificationDelivery
from core.notifications.selectors.inbox import notification_unread_count
from core.users.models import User


def _push_read(*, user: User, notification_id: str | None, updated: int) -> None:
    unread = notification_unread_count(user=user)
    realtime_publish(
        user_id=user.id,
        payload={
            "type": "read",
            "unread_count": unread,
            "notification_id": notification_id,
            "updated": updated,
        },
    )


@transaction.atomic
def notification_mark_read(*, user: User, notification_id: UUID) -> NotificationDelivery:
    row = get_object_or_404(
        NotificationDelivery,
        pk=notification_id,
        user=user,
        channel=CHANNEL_IN_APP,
        status=STATUS_SENT,
        deleted_at__isnull=True,
    )
    if row.read_at is None:
        row.read_at = timezone.now()
        row.save(update_fields=["read_at", "updated_at"])
        transaction.on_commit(lambda: _push_read(user=user, notification_id=str(row.id), updated=1))
    return row


@transaction.atomic
def notification_mark_read_all(*, user: User) -> int:
    now = timezone.now()
    updated = NotificationDelivery.objects.filter(
        user=user,
        channel=CHANNEL_IN_APP,
        status=STATUS_SENT,
        read_at__isnull=True,
        deleted_at__isnull=True,
    ).update(read_at=now, updated_at=now)
    if updated:
        transaction.on_commit(lambda: _push_read(user=user, notification_id=None, updated=updated))
    return updated
