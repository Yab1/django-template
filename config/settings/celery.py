from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from kombu import Exchange, Queue

from config.env import env

# https://docs.celeryproject.org/en/stable/userguide/configuration.html

CELERY_BROKER_URL = env(
    "CELERY_BROKER_URL",
    default="amqp://guest:guest@localhost:5672/vendor_management",
)  # type: ignore
CELERY_RESULT_BACKEND = "django-db"

CELERY_TIMEZONE = "UTC"

CELERY_TASK_SOFT_TIME_LIMIT = 20  # seconds
CELERY_TASK_TIME_LIMIT = 30  # seconds
CELERY_TASK_MAX_RETRIES = 3

# Queue isolation for this project (override via env-friendly names later if needed)
CELERY_TASK_DEFAULT_QUEUE = "vendor_management"
CELERY_TASK_DEFAULT_EXCHANGE = "vendor_management"
CELERY_TASK_DEFAULT_ROUTING_KEY = "vendor_management"

CELERY_TASK_QUEUES = (
    Queue(
        "vendor_management",
        Exchange("vendor_management", type="direct"),
        routing_key="vendor_management",
    ),
)

CELERY_TASK_ROUTES = {}

CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ACKS_LATE = True

CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# App-specific periodic tasks go here when added.
CELERY_BEAT_SCHEDULE: dict = {}

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.base")

app = Celery("vendor_management")

app.conf.timezone = "UTC"
app.conf.enable_utc = True

app.config_from_object("django.conf:settings", namespace="CELERY")

app.conf.broker_connection_retry_on_startup = True

app.autodiscover_tasks()
