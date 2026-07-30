"""
Test settings for pytest-django.

This module provides optimized settings for running tests with pytest.
It uses in-memory SQLite for faster test execution and disables
unnecessary features that slow down tests.
"""

from config.django.base import *  # noqa

# Use in-memory database for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}


# Disable migrations for faster test setup
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

# Disable file storage (use in-memory for tests)
DEFAULT_FILE_STORAGE = "django.core.files.storage.InMemoryStorage"

# Disable caching for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
}

# Disable email sending in tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
