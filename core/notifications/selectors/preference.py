from core.notifications.constants import CATEGORIES, CHANNELS, DEFAULT_CHANNEL_ENABLED
from core.notifications.models import NotificationPreference
from core.notifications.services.gate import is_mandatory
from core.users.models import User


def notification_preference_list(*, user: User) -> list[NotificationPreference]:
    return list(
        NotificationPreference.objects.filter(user=user, deleted_at__isnull=True).order_by(
            "channel",
            "category",
        ),
    )


def notification_preference_effective(*, user: User) -> list[dict]:
    stored = {(row.channel, row.category): row for row in notification_preference_list(user=user)}
    items: list[dict] = []
    for channel in CHANNELS:
        for category in CATEGORIES:
            row = stored.get((channel, category))
            default_enabled = DEFAULT_CHANNEL_ENABLED.get(channel, False)
            mandatory = is_mandatory(channel=channel, category=category)
            enabled = True if mandatory else (row.enabled if row is not None else default_enabled)
            items.append({
                "channel": channel,
                "category": category,
                "enabled": enabled,
                "default_enabled": default_enabled,
                "mandatory": mandatory,
                "destination": row.destination if row is not None else "",
                "stored": row is not None,
            })
    return items
