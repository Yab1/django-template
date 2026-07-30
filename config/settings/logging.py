import logging
import os
import re

from config.env import BASE_DIR, env

# Ensure logs directory exists
os.makedirs(f"{BASE_DIR}/logs", exist_ok=True)

# Environment-aware log levels
# In production (DEBUG=False), use INFO. In development, use DEBUG.
DEBUG_MODE = env.bool("DJANGO_DEBUG", default=True)  # type: ignore
LOG_LEVEL = "DEBUG" if DEBUG_MODE else "INFO"


# ANSI color codes
class Colors:
    RESET = "\033[0m"

    # Date colors
    DATE = "\033[36m"  # Cyan

    # Log level colors
    DEBUG = "\033[36m"  # Cyan
    INFO = "\033[34m"  # Blue
    WARNING = "\033[33m"  # Yellow
    ERROR = "\033[31m"  # Red
    CRITICAL = "\033[35m"  # Magenta

    # Other colors
    NAME = "\033[90m"  # Dark gray


class TemporalActivityRetryFilter(logging.Filter):
    """
    Cleans up two categories of Temporal activity failure noise:

    1. Intentional retry gates (RuntimeError ending in 'Retrying.'):
       Downgrade to DEBUG and strip traceback — these are expected polling loops,
       not real errors (e.g. waiting for vitals to be recorded).

    2. Missing handler errors (UnknownActivityHandlerError):
       Keep at WARNING but strip the 10-line Temporal SDK stacktrace — the error
       message itself is already actionable ('Register one with @workflow_activity').
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if "Completing activity as failed" not in str(record.getMessage()):
            return True
        exc_info = record.exc_info
        if exc_info and exc_info[1] is not None:
            exc = exc_info[1]
            msg = str(exc)
            if msg.rstrip().endswith("Retrying."):
                record.levelno = logging.DEBUG
                record.levelname = "DEBUG"
                record.exc_info = None
                record.exc_text = None
            elif type(exc).__name__ == "UnknownActivityHandlerError":
                record.exc_info = None
                record.exc_text = None
        return True


class TemporalWorkflowCompletionFilter(logging.Filter):
    """
    Temporal logs 'Workflow raised failure' with a CancelledError traceback when a
    workflow completes normally — the event loop cancels the wait_condition coroutine
    as part of teardown. This is not a real failure. Rewrite those records to a clear
    completion message and drop the misleading traceback.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if "Workflow raised failure" not in str(record.getMessage()):
            return True
        exc_info = record.exc_info
        if exc_info and exc_info[0] is not None:
            import asyncio

            import temporalio.exceptions

            if issubclass(exc_info[0], asyncio.CancelledError) or issubclass(
                exc_info[0],
                temporalio.exceptions.CancelledError,
            ):
                record.msg = "Workflow run ended (wait_condition cancelled — normal teardown, not a failure)"
                record.args = ()
                record.exc_info = None
                record.exc_text = None
        return True


class SensitiveDataFilter(logging.Filter):
    """Filter sensitive data (passwords, tokens) from log messages using regex."""

    SENSITIVE_PATTERNS = [
        (r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]?([^'\"]+)['\"]?", r"\1=***"),
        (r"(?i)(token|api_key|apikey|secret|secret_key)\s*[:=]\s*['\"]?([^'\"]+)['\"]?", r"\1=***"),
        (r"(?i)(authorization|bearer)\s+([a-zA-Z0-9\-_\.]+)", r"\1 ***"),
    ]

    def filter(self, record):
        """Filter sensitive data from log messages."""
        if hasattr(record, "msg") and record.msg:
            original_msg = str(record.msg)
            filtered_msg = original_msg

            for pattern, replacement in self.SENSITIVE_PATTERNS:
                filtered_msg = re.sub(pattern, replacement, filtered_msg, flags=re.IGNORECASE)

            if filtered_msg != original_msg:
                record.msg = filtered_msg

        return True


class ColoredFormatter(logging.Formatter):
    """Simple colored formatter - no boxes, just colored text."""

    COLORS = {
        "DEBUG": Colors.DEBUG,
        "INFO": Colors.INFO,
        "WARNING": Colors.WARNING,
        "ERROR": Colors.ERROR,
        "CRITICAL": Colors.CRITICAL,
    }

    def format(self, record):
        # Store original values
        original_levelname = record.levelname
        original_name = record.name

        # Get color for log level
        level_color = self.COLORS.get(record.levelname, Colors.RESET)

        # Color the date
        date_str = self.formatTime(record, self.datefmt)
        colored_date = f"{Colors.DATE}{date_str}{Colors.RESET}"

        # Color the level name
        colored_level = f"{level_color}{record.levelname}{Colors.RESET}"

        # Color the logger name
        colored_name = f"{Colors.NAME}{record.name}{Colors.RESET}"

        # Temporarily set colored values on record
        record.levelname = colored_level
        record.asctime = colored_date
        record.name = colored_name

        # Use parent format method which handles all the formatting correctly
        try:
            msg = super().format(record)
        finally:
            # Restore original values
            record.levelname = original_levelname
            record.name = original_name

        return msg


# Formatters - Simple with colors (no boxes)
FORMATTERS = {
    "verbose": {
        "()": ColoredFormatter,
        "format": (
            "%(levelname)s %(asctime)s [%(process)d:%(thread)d] %(name)s.%(funcName)s:%(lineno)d - %(message)s"  # noqa: E501
        ),
        "datefmt": "%Y-%m-%d %H:%M:%S",
    },
    "simple": {
        "()": ColoredFormatter,
        "format": "%(levelname)s %(asctime)s %(name)s - %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S",
    },
    "plain": {
        "format": "%(levelname)s %(asctime)s %(name)s - %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S",
    },
}

# Filters for professional logging
FILTERS = {
    "sensitive_data": {
        "()": SensitiveDataFilter,
    },
    "temporal_workflow_completion": {
        "()": TemporalWorkflowCompletionFilter,
    },
    "temporal_activity_retry": {
        "()": TemporalActivityRetryFilter,
    },
}

# Handlers - Environment-aware configuration
# Console handler (always enabled for both local and production)
HANDLERS = {
    "console_handler": {
        "class": "logging.StreamHandler",
        "formatter": "simple",
        "level": "DEBUG",
        "filters": ["sensitive_data", "temporal_workflow_completion", "temporal_activity_retry"],
    },
}

# File handlers (only for local development)
# In production, Promtail reads Docker container logs (stdout/stderr)
if DEBUG_MODE:
    HANDLERS.update({
        "file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"{BASE_DIR}/logs/django.log",
            "mode": "a",
            "formatter": "plain",  # No colors in file logs
            "level": LOG_LEVEL,
            "backupCount": 10,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "encoding": "utf-8",
            "filters": ["sensitive_data"],
        },
        "detailed_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"{BASE_DIR}/logs/django_detailed.log",
            "mode": "a",
            "formatter": "plain",  # No colors in file logs
            "level": "DEBUG",
            "backupCount": 10,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "encoding": "utf-8",
            "filters": ["sensitive_data"],
        },
        "error_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"{BASE_DIR}/logs/errors.log",
            "mode": "a",
            "formatter": "plain",  # No colors in file logs
            "level": "ERROR",
            "backupCount": 20,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "encoding": "utf-8",
            "filters": ["sensitive_data"],
        },
    })

# Loggers - Environment-aware configuration
# Base handlers: console always, file handlers only in local
if DEBUG_MODE:
    # Local development: console + file handlers
    root_handlers = ["console_handler", "file_handler"]
    django_handlers = ["console_handler", "detailed_file_handler"]
    request_handlers = ["console_handler", "error_file_handler"]
    server_handlers = ["console_handler", "file_handler"]
    db_handlers = ["detailed_file_handler"]
    security_handlers = ["console_handler", "error_file_handler"]
    app_handlers = ["console_handler", "detailed_file_handler"]
    third_party_handlers = ["console_handler", "file_handler"]
    audit_handlers = ["console_handler", "detailed_file_handler"]
else:
    # Production: console only (Promtail reads Docker container logs)
    root_handlers = ["console_handler"]
    django_handlers = ["console_handler"]
    request_handlers = ["console_handler"]
    server_handlers = ["console_handler"]
    db_handlers = ["console_handler"]
    security_handlers = ["console_handler"]
    app_handlers = ["console_handler"]
    third_party_handlers = ["console_handler"]
    audit_handlers = ["console_handler"]

LOGGERS = {
    # Root logger - Environment-aware level
    "": {
        "handlers": root_handlers,
        "level": LOG_LEVEL,
    },
    # Django core loggers
    "django": {
        "handlers": django_handlers,
        "level": "INFO",
        "propagate": False,
    },
    "django.request": {
        "handlers": request_handlers,
        "level": "WARNING",
        "propagate": False,
    },
    "django.server": {
        "handlers": server_handlers,
        "level": "INFO",
        "propagate": False,
    },
    "django.db.backends": {
        "handlers": db_handlers,
        "level": "WARNING",
        "propagate": False,
    },
    "django.security": {
        "handlers": security_handlers,
        "level": "WARNING",
        "propagate": False,
    },
    # Application loggers
    "core": {
        "handlers": app_handlers,
        "level": "DEBUG",
        "propagate": False,
    },
    # Third-party loggers
    "celery": {
        "handlers": third_party_handlers,
        "level": "INFO",
        "propagate": False,
    },
    "temporalio": {
        "handlers": third_party_handlers,
        "level": "WARNING",
        "propagate": False,
    },
    # Security and audit
    "security": {
        "handlers": security_handlers,
        "level": "INFO",
        "propagate": False,
    },
    "audit": {
        "handlers": audit_handlers,
        "level": "INFO",
        "propagate": False,
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": FORMATTERS,
    "filters": FILTERS,
    "handlers": HANDLERS,
    "loggers": LOGGERS,
}

__all__ = ["LOGGING"]
