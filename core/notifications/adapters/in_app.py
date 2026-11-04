import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from core.notifications.adapters.base import Outbound

logger = logging.getLogger(__name__)


def user_notification_group(user_id) -> str:
    return f"notifications.user.{user_id}"


class InAppSender:
    """Inbox row is already persisted. Push a live frame if a socket is open."""

    def send(self, *, outbound: Outbound) -> str | None:
        return None


def realtime_publish(*, user_id, payload: dict) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    try:
        async_to_sync(layer.group_send)(
            user_notification_group(user_id),
            {"type": "notification.event", "payload": payload},
        )
    except Exception:
        logger.exception("In-app websocket publish failed user_id=%s", user_id)
