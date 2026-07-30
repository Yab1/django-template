"""Types for the systems app."""

from dataclasses import dataclass
from typing import Literal

MinioHealthStatus = Literal["ok", "error", "not_configured"]
RabbitmqHealthStatus = Literal["ok", "error", "not_configured"]


@dataclass(frozen=True, slots=True)
class SystemHealthCheck:
    """Result of a system health probe (database, cache, RabbitMQ, optional MinIO)."""

    status: Literal["ok", "unhealthy"]
    database: Literal["ok", "error"]
    cache: Literal["ok", "error"]
    rabbitmq: RabbitmqHealthStatus
    minio: MinioHealthStatus
