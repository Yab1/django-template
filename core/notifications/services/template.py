from uuid import UUID

from django.shortcuts import get_object_or_404

from core.notifications.models import NotificationTemplate


def notification_template_update(*, template_id: UUID, data: dict) -> NotificationTemplate:
    row = get_object_or_404(NotificationTemplate, pk=template_id, deleted_at__isnull=True)
    for field in ("subject", "body", "format", "is_active"):
        if field in data and data[field] is not None:
            setattr(row, field, data[field])
    row.full_clean()
    row.save()
    return row
