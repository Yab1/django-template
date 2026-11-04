"""
App-specific Django settings.

All custom settings that use DJANGO_*-prefixed environment variables
should live here. Base settings (config/django/base.py) import this module.
"""

# pyright: reportArgumentType=false

from config.env import env


def get_app_public_base_url() -> str:
    """Public API base URL (no trailing slash). Used for APP_DOMAIN and OpenAPI servers."""
    raw = str(env.str("DJANGO_APP_DOMAIN", default="localhost")).strip()
    port = str(env.str("DJANGO_APP_PORT", default="")).strip()

    if "://" in raw:
        return raw.rstrip("/")

    local = raw in ("localhost", "127.0.0.1")
    if not port:
        port = "8000" if local else ""

    scheme = "https" if port == "443" else "http"

    if not port or port in ("80", "443"):
        netloc = raw
    else:
        netloc = f"{raw}:{port}"

    return f"{scheme}://{netloc}".rstrip("/")


APP_DOMAIN = get_app_public_base_url()

APP_NAME = env.str("DJANGO_APP_NAME", default="django-template")

FRONTEND_URL = env.str("DJANGO_FRONTEND_URL", default="http://localhost:3000").rstrip("/")  # type: ignore[assignment]

ENVIRONMENT = env.str("DJANGO_ENVIRONMENT", default="development")

REFERENCE_ID_PLATFORM_PREFIX = env("DJANGO_REFERENCE_ID_PLATFORM_PREFIX", default="DT")

# Default DRF permission. Individual views can still set AllowAny / IsAuthenticated.
AUTH_REQUIRED = env.bool("DJANGO_AUTH_REQUIRED", default=True)

# Catalog permission checks (roles/codes). Off until ``core.security`` app is fully ported.
# false = any authenticated active user passes every permission code. Local/dev only.
PERMISSIONS_ENABLED = env.bool("DJANGO_PERMISSIONS_ENABLED", default=False)

# DRF throttles (anon ≈ login/token, user ≈ authenticated reads). Off by default.
RATE_LIMIT_ENABLED = env.bool("DJANGO_RATE_LIMIT_ENABLED", default=False)
RATE_LIMIT_AUTH = env.int("DJANGO_RATE_LIMIT_AUTH", default=10)
RATE_LIMIT_WRITE = env.int("DJANGO_RATE_LIMIT_WRITE", default=120)
RATE_LIMIT_READ = env.int("DJANGO_RATE_LIMIT_READ", default=600)

# Skip load_superusers when false (deploy seed stage still calls the command).
SEED_ENABLED = env.bool("DJANGO_SEED_ENABLED", default=True)

# CIDRs / IPs that may send X-Forwarded-For. Empty = trust REMOTE_ADDR only.
TRUSTED_PROXIES = env.list("DJANGO_TRUSTED_PROXIES", default=[])


def get_app_version() -> str:
    """Installed package version, or pyproject fallback when running from a source tree."""
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("django-template")
    except PackageNotFoundError:
        return "0.1.0"


APP_VERSION = get_app_version()
