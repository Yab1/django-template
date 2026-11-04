from django.db.models import QuerySet

from core.notifications.models import NotificationTemplate


def notification_template_list() -> QuerySet[NotificationTemplate]:
    return NotificationTemplate.objects.filter(deleted_at__isnull=True).order_by(
        "channel",
        "category",
        "locale",
    )
