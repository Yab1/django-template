import os

# Gunicorn configuration for Django + Uvicorn ASGI

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '6000')}"
backlog = int(os.environ.get("GUNICORN_BACKLOG", "1024"))

# Worker processes
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = int(os.environ.get("GUNICORN_WORKER_CONNECTIONS", "500"))
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", "100"))
preload_app = os.environ.get("GUNICORN_PRELOAD_APP", "True").lower() == "true"

# Increased for long-lived WebSocket connections
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "300"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", "30"))

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

proc_name = os.environ.get("GUNICORN_PROC_NAME", "django_template_gunicorn")

# Security
limit_request_line = int(os.environ.get("GUNICORN_LIMIT_REQUEST_LINE", "4094"))
limit_request_fields = int(os.environ.get("GUNICORN_LIMIT_REQUEST_FIELDS", "100"))
limit_request_field_size = int(os.environ.get("GUNICORN_LIMIT_REQUEST_FIELD_SIZE", "8190"))

# Performance
worker_tmp_dir = "/tmp"

# Environment
raw_env = [
    "DJANGO_SETTINGS_MODULE=config.django.base",
]

# Server settings
reload = os.environ.get("GUNICORN_RELOAD", "False").lower() == "true"
