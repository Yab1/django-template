# pyright: reportArgumentType=false
"""
Django cache backend (Redis via django-redis).

Set ``DJANGO_CACHE_REDIS_URL`` to your Redis instance. Default is local Redis DB 1
so it stays separate from other tools that often use DB 0. For password auth use a URL
such as ``redis://:password@host:6379/1``.

Test settings override this with ``DummyCache`` (see ``config/django/test.py``).
"""

from config.env import env

DJANGO_CACHE_REDIS_URL = env.str("DJANGO_CACHE_REDIS_URL", default="redis://127.0.0.1:6379/1")

DJANGO_CACHE_REDIS_MAX_CONNECTIONS = env.int("DJANGO_CACHE_REDIS_MAX_CONNECTIONS", default=50)
DJANGO_CACHE_REDIS_SOCKET_CONNECT_TIMEOUT = env.int("DJANGO_CACHE_REDIS_SOCKET_CONNECT_TIMEOUT", default=5)
DJANGO_CACHE_REDIS_SOCKET_TIMEOUT = env.int("DJANGO_CACHE_REDIS_SOCKET_TIMEOUT", default=5)
DJANGO_CACHE_REDIS_HEALTH_CHECK_INTERVAL = env.int("DJANGO_CACHE_REDIS_HEALTH_CHECK_INTERVAL", default=30)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": DJANGO_CACHE_REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_CLASS": "redis.connection.ConnectionPool",
            "CONNECTION_POOL_CLASS_KWARGS": {
                "max_connections": DJANGO_CACHE_REDIS_MAX_CONNECTIONS,
                "retry_on_timeout": True,
            },
            "SOCKET_CONNECT_TIMEOUT": DJANGO_CACHE_REDIS_SOCKET_CONNECT_TIMEOUT,
            "SOCKET_TIMEOUT": DJANGO_CACHE_REDIS_SOCKET_TIMEOUT,
            "HEALTH_CHECK_INTERVAL": DJANGO_CACHE_REDIS_HEALTH_CHECK_INTERVAL,
        },
        "KEY_PREFIX": "ehr",
    },
}
