"""Read-only queries for system / infrastructure health checks."""

import logging
from typing import Literal

from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.db import connection

from core.systems.types import MinioHealthStatus, RabbitmqHealthStatus, SystemHealthCheck

logger = logging.getLogger(__name__)

_HEALTHCHECK_CACHE_KEY = "__systems_healthcheck__"


def system_health_get() -> SystemHealthCheck:
    """
    Return connectivity status for database, cache, RabbitMQ, and MinIO (when used).

    Does not raise; failed checks are reported as ``error`` component status.
    ``minio`` is ``not_configured`` when the default file storage backend is not MinIO.
    ``rabbitmq`` is ``not_configured`` when ``CELERY_BROKER_URL`` is empty or Celery eager mode is on.
    Overall ``status`` is ``ok`` only when every probed component is ``ok`` or ``not_configured``.
    """
    database: Literal["ok", "error"] = _check_database()
    cache_status: Literal["ok", "error"] = _check_cache()
    rabbitmq_status: RabbitmqHealthStatus = _check_rabbitmq()
    minio_status: MinioHealthStatus = _check_minio()
    overall: Literal["ok", "unhealthy"] = (
        "unhealthy"
        if any(s == "error" for s in (database, cache_status, rabbitmq_status, minio_status))
        else "ok"
    )
    result = SystemHealthCheck(
        status=overall,
        database=database,
        cache=cache_status,
        rabbitmq=rabbitmq_status,
        minio=minio_status,
    )
    if overall == "unhealthy":
        logger.warning(
            "System health check unhealthy: database=%s cache=%s rabbitmq=%s minio=%s",
            database,
            cache_status,
            rabbitmq_status,
            minio_status,
        )
    return result


def _check_database() -> Literal["ok", "error"]:
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return "error"
    return "ok"


def _check_cache() -> Literal["ok", "error"]:
    try:
        cache.set(_HEALTHCHECK_CACHE_KEY, "1", timeout=10)
        if cache.get(_HEALTHCHECK_CACHE_KEY) != "1":
            return "error"
        cache.delete(_HEALTHCHECK_CACHE_KEY)
    except Exception:
        return "error"
    return "ok"


_RABBITMQ_CONNECT_TIMEOUT_SEC = 3.0


def _check_rabbitmq() -> RabbitmqHealthStatus:
    """
    Verify the Celery broker (RabbitMQ) accepts an AMQP connection.

    Skipped when ``CELERY_TASK_ALWAYS_EAGER`` is enabled (pytest) or the broker URL is unset.
    """
    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        return "not_configured"
    broker_url = (getattr(settings, "CELERY_BROKER_URL", None) or "").strip()
    if not broker_url:
        return "not_configured"
    try:
        from kombu import Connection

        with Connection(broker_url, connect_timeout=_RABBITMQ_CONNECT_TIMEOUT_SEC) as conn:
            conn.ensure_connection(max_retries=1)
    except Exception:
        return "error"
    return "ok"


def _check_minio() -> MinioHealthStatus:
    """
    When default storage is MinIO-backed, verify the MinIO client is usable.

    Returns ``not_configured`` when another storage backend is active.
    If the media bucket is missing and auto-create is enabled, attempts ``make_bucket``.
    """
    backend = (settings.STORAGES.get("default") or {}).get("BACKEND") or ""
    if "minio" not in backend.lower():
        return "not_configured"
    try:
        client = getattr(default_storage, "client", None)
        bucket_name = getattr(default_storage, "bucket_name", None)
        if client is None or not bucket_name:
            return "error"
        if client.bucket_exists(bucket_name):
            return "ok"
        auto_create = getattr(settings, "MINIO_STORAGE_AUTO_CREATE_MEDIA_BUCKET", False)
        if auto_create:
            try:
                client.make_bucket(bucket_name)
            except Exception:
                pass
            return "ok" if client.bucket_exists(bucket_name) else "error"
        return "ok"
    except Exception:
        return "error"
