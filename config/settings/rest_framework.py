"""
Django REST framework configuration.

Includes optional features: browsable API (Markdown, Pygments), filtering (django-filter),
OpenAPI 3 / Swagger via drf-spectacular, and object-level permissions (django-guardian).
"""

from config.settings.app import (
    AUTH_REQUIRED,
    RATE_LIMIT_AUTH,
    RATE_LIMIT_ENABLED,
    RATE_LIMIT_READ,
    RATE_LIMIT_WRITE,
)

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.api.exception_handlers.drf_default_with_modifications_exception_handler",
    "DEFAULT_RENDERER_CLASSES": [
        "core.api.renderers.EnvelopeJSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated" if AUTH_REQUIRED else "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    # Serialize Decimal as JSON numbers (not strings like "1.0000000000" or "0E-10").
    "COERCE_DECIMAL_TO_STRING": False,
}

if RATE_LIMIT_ENABLED:
    REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ]
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
        "anon": f"{RATE_LIMIT_AUTH}/min",
        "user": f"{RATE_LIMIT_READ}/min",
        "write": f"{RATE_LIMIT_WRITE}/min",
    }
