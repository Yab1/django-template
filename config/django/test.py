"""
Test settings for pytest-django.

This module provides optimized settings for running tests with pytest.
The test database inherits from base settings so we run against the same
backend as production (PostgreSQL). SQLite is not viable here because
several models in this codebase use Postgres-only constructs
(e.g. ``django.contrib.postgres.fields.ArrayField`` with ``size=``,
JSONB-backed fields, ``UniqueConstraint(condition=...)``, etc.) that
SQLite cannot create.

Django will create/drop a ``test_<DJANGO_DB_NAME>`` database automatically
on first run; with ``--reuse-db`` it is kept between runs for speed.
"""

from config.django.base import *  # noqa

# DATABASES intentionally NOT overridden here -- inherit Postgres from base.


# Disable migrations for faster test setup. The schema is built from model
# definitions via sync_apps, which is fine because we run against Postgres.
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Disable external services
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Faster password hashing for tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Disable logging during tests (unless needed for debugging)
LOGGING_CONFIG = None

# Disable middleware that's not needed for tests
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

# Test-specific settings
TENANT_ROUTING_ENABLED = False  # Disable tenant routing in tests

# Disable debug toolbar in tests
DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: False}

# Disable silk in tests
SILK_ENABLED = False

# Disable file storage (use in-memory for tests)
DEFAULT_FILE_STORAGE = "django.core.files.storage.InMemoryStorage"

# Disable caching for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
}

# Single-process tests: no Redis channel layer required
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# Disable email sending in tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
