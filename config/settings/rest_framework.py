"""
Django REST framework configuration.

Includes optional features: browsable API (Markdown, Pygments), filtering (django-filter),
OpenAPI 3 / Swagger via drf-spectacular, and object-level permissions (django-guardian).
"""

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
        "rest_framework.permissions.IsAuthenticated",
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
