from django.urls import path

from core.notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
    path("api/v1/notifications/stream/", NotificationConsumer.as_asgi()),
]
