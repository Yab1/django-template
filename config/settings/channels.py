# pyright: reportArgumentType=false
"""
Django Channels layer (WebSocket fan-out).

``InMemoryChannelLayer`` only works inside a single process. ``make dev`` runs
Daphne (WS consumers) and Celery (``InAppAdapter`` → ``realtime_publish``) in
separate processes, so Redis is required for in-app notification pushes to reach
open sockets.

Use a dedicated Redis DB (default ``/2``) so channel keys stay separate from
``DJANGO_CACHE_REDIS_URL`` (typically ``/1``).

Local Docker Redis is often ``127.0.0.1:7377`` — mirror the host/password from
cache URL and change the DB index.
"""

from config.env import env

DJANGO_CHANNEL_REDIS_URL = env.str(
    "DJANGO_CHANNEL_REDIS_URL",
    default="redis://127.0.0.1:6379/2",
)

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [DJANGO_CHANNEL_REDIS_URL],
        },
    },
}
