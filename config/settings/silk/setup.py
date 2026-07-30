import logging

from django.urls import include, path

logger = logging.getLogger("configuration")


def _is_silk_enabled() -> bool:
    from .settings import SILK_ENABLED

    if not SILK_ENABLED:
        return False

    try:
        import silk  # noqa: F401
    except ImportError:
        logger.info("No installation found for: django-silk")
        return False

    return True


class SilkSetup:
    """Namespaced helpers for wiring django-silk into settings and URLs."""

    @staticmethod
    def do_settings(INSTALLED_APPS, MIDDLEWARE):  # noqa: N803
        enabled = _is_silk_enabled()
        logger.info(f"Django Silk in use: {enabled}")

        if not enabled:
            return INSTALLED_APPS, MIDDLEWARE

        INSTALLED_APPS = INSTALLED_APPS + ["silk"]  # noqa: N806

        # SilkyMiddleware must sit near the top so it can time the full request.
        # Place it right after SecurityMiddleware and CorsMiddleware.
        silk_middleware = "silk.middleware.SilkyMiddleware"
        _middleware = MIDDLEWARE[::]
        try:
            insert_after = _middleware.index("corsheaders.middleware.CorsMiddleware")
            _middleware.insert(insert_after + 1, silk_middleware)
        except ValueError:
            _middleware.insert(0, silk_middleware)

        MIDDLEWARE = _middleware  # noqa: N806
        return INSTALLED_APPS, MIDDLEWARE

    @staticmethod
    def do_urls(urlpatterns):
        if not _is_silk_enabled():
            return urlpatterns

        return urlpatterns + [path("silk/", include("silk.urls", namespace="silk"))]
