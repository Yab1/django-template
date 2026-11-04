from django.conf import settings

from core.notifications.adapters.base import Outbound, Sender
from core.notifications.adapters.email import EmailSender
from core.notifications.adapters.in_app import InAppSender, realtime_publish, user_notification_group
from core.notifications.adapters.telegram import TelegramSender
from core.notifications.adapters.webhook import WebhookSender
from core.notifications.constants import (
    CHANNEL_EMAIL,
    CHANNEL_IN_APP,
    CHANNEL_PUSH,
    CHANNEL_SMS,
    CHANNEL_TELEGRAM,
)


def channel_senders() -> dict[str, Sender]:
    """Register senders only when the channel flag and credentials are present."""
    senders: dict[str, Sender] = {}
    if getattr(settings, "NOTIFICATION_IN_APP_ENABLED", True):
        senders[CHANNEL_IN_APP] = InAppSender()
    if getattr(settings, "NOTIFICATION_EMAIL_ENABLED", False) and getattr(settings, "MAIL_ENABLED", True):
        senders[CHANNEL_EMAIL] = EmailSender()
    sms_url = (getattr(settings, "SMS_PROVIDER_URL", "") or "").strip()
    if getattr(settings, "NOTIFICATION_SMS_ENABLED", False) and sms_url:
        senders[CHANNEL_SMS] = WebhookSender(
            url=sms_url,
            token=getattr(settings, "SMS_PROVIDER_TOKEN", "") or "",
        )
    push_url = (getattr(settings, "PUSH_PROVIDER_URL", "") or "").strip()
    if getattr(settings, "NOTIFICATION_PUSH_ENABLED", False) and push_url:
        senders[CHANNEL_PUSH] = WebhookSender(
            url=push_url,
            token=getattr(settings, "PUSH_PROVIDER_TOKEN", "") or "",
        )
    telegram_token = (getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip()
    if getattr(settings, "NOTIFICATION_TELEGRAM_ENABLED", False) and telegram_token:
        senders[CHANNEL_TELEGRAM] = TelegramSender(bot_token=telegram_token)
    return senders


__all__ = [
    "Outbound",
    "Sender",
    "channel_senders",
    "realtime_publish",
    "user_notification_group",
]
