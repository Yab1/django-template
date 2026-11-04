from json import JSONDecodeError

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from core.notifications.adapters.in_app import user_notification_group
from core.notifications.selectors.inbox import notification_unread_count


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """Live inbox: ``ready``, then ``notification`` / ``read`` events from the channel layer."""

    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        # Postman and some clients send empty/binary frames. Ignore junk; JSON may arrive as bytes.
        if not text_data and bytes_data:
            try:
                text_data = bytes_data.decode("utf-8")
            except UnicodeDecodeError:
                return
        if not (text_data or "").strip():
            return
        try:
            content = await self.decode_json(text_data)
        except (JSONDecodeError, ValueError, TypeError):
            return
        await self.receive_json(content, **kwargs)

    async def connect(self):
        user = self.scope.get("user")
        if user is None or getattr(user, "is_anonymous", True):
            await self.close(code=4401)
            return
        self.user = user
        self.group_name = user_notification_group(user.id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        unread = await self._unread()
        await self.send_json({"type": "ready", "unread_count": unread})

    async def disconnect(self, code):
        if getattr(self, "group_name", None):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") == "resync":
            unread = await self._unread()
            await self.send_json({"type": "ready", "unread_count": unread})

    async def notification_event(self, event):
        await self.send_json(event.get("payload") or {})

    async def _unread(self) -> int:
        from channels.db import database_sync_to_async

        return await database_sync_to_async(notification_unread_count)(user=self.user)
