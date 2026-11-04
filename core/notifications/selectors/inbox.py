from django.db.models import QuerySet

from core.notifications.constants import CHANNEL_IN_APP, STATUS_SENT
from core.notifications.models import NotificationDelivery
from core.users.models import User


def notification_inbox_list(*, user: User, unread: bool = False) -> QuerySet[NotificationDelivery]:
    qs = NotificationDelivery.objects.filter(
        user=user,
        channel=CHANNEL_IN_APP,
        status=STATUS_SENT,
        deleted_at__isnull=True,
        is_visible=True,
    )
    if unread:
        qs = qs.filter(read_at__isnull=True)
    return qs.order_by("-created_at")


def notification_unread_count(*, user: User) -> int:
    return notification_inbox_list(user=user, unread=True).count()
