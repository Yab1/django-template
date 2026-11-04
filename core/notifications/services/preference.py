from django.core.exceptions import ValidationError

from core.notifications.constants import CATEGORIES, CHANNELS
from core.notifications.models import NotificationPreference
from core.notifications.services.gate import is_mandatory
from core.users.models import User


def notification_preference_upsert(*, user: User, items: list[dict]) -> list[NotificationPreference]:
    saved: list[NotificationPreference] = []
    for item in items:
        channel = item["channel"]
        category = item["category"]
        if channel not in CHANNELS or category not in CATEGORIES:
            raise ValidationError("Unknown channel or category.")
        enabled = bool(item.get("enabled", True))
        if not enabled and is_mandatory(channel=channel, category=category):
            raise ValidationError("This preference cannot be disabled.")
        destination = str(item.get("destination") or "")
        row, _created = NotificationPreference.objects.update_or_create(
            user=user,
            channel=channel,
            category=category,
            deleted_at=None,
            defaults={"enabled": enabled, "destination": destination},
        )
        row.full_clean()
        row.save()
        saved.append(row)
    return saved
