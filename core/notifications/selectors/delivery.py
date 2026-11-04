from typing import Any
from uuid import UUID

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from core.notifications.models import NotificationDelivery


def notification_delivery_list(*, filters: dict[str, Any] | None = None) -> QuerySet[NotificationDelivery]:
    qs = NotificationDelivery.objects.filter(deleted_at__isnull=True).select_related("user", "template")
    filters = filters or {}
    if filters.get("user_id"):
        qs = qs.filter(user_id=filters["user_id"])
    if filters.get("channel"):
        qs = qs.filter(channel=filters["channel"])
    if filters.get("status"):
        qs = qs.filter(status=filters["status"])
    if filters.get("category"):
        qs = qs.filter(category=filters["category"])
    return qs.order_by("-created_at")


def notification_delivery_get(*, delivery_id: UUID) -> NotificationDelivery:
    return get_object_or_404(
        NotificationDelivery.objects.select_related("user", "template").prefetch_related("attempt_log"),
        pk=delivery_id,
        deleted_at__isnull=True,
    )
