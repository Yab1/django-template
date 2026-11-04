from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from core.notifications.constants import STATUS_FAILED, STATUS_PENDING
from core.notifications.models import NotificationDelivery
from core.notifications.selectors.delivery import notification_delivery_get


@transaction.atomic
def notification_delivery_retry(*, delivery_id: UUID) -> NotificationDelivery:
    row = notification_delivery_get(delivery_id=delivery_id)
    if row.status != STATUS_FAILED:
        raise ValidationError("Only failed deliveries can be retried.")
    row.status = STATUS_PENDING
    row.next_attempt_at = timezone.now()
    row.last_error = ""
    row.locked_until = None
    row.save(update_fields=["status", "next_attempt_at", "last_error", "locked_until", "updated_at"])
    from core.notifications.services.notify import _kick_dispatch

    transaction.on_commit(_kick_dispatch)
    return row
