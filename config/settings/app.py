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
        port = "7000" if local else ""

    scheme = "https" if port == "443" else "http"

    if not port or port in ("80", "443"):
        netloc = raw
    else:
        netloc = f"{raw}:{port}"

    return f"{scheme}://{netloc}".rstrip("/")


APP_DOMAIN = get_app_public_base_url()

FRONTEND_URL = env.str("DJANGO_FRONTEND_URL", default="http://localhost:3000").rstrip("/")  # type: ignore[assignment]

REFERENCE_ID_PLATFORM_PREFIX = env("DJANGO_REFERENCE_ID_PLATFORM_PREFIX", default="VM")
