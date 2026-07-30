"""
Django GUID Configuration

Configures django-guid for request ID tracking in logs.
See: https://django-guid.readthedocs.io/
"""

# Django GUID Settings
DJANGO_GUID = {
    # GUID format: 'uuid' (default) or 'string'
    "GUID_HEADER_NAME": "Correlation-ID",
    # Skip GUID generation for certain paths (health checks, etc.)
    "SKIP_CLEANUP": False,
    # Return GUID in response header
    "RETURN_HEADER": True,
    # Expose GUID in logs (adds correlation_id to log records)
    "EXPOSE_HEADER": True,
    # Skip GUID for certain paths
    "IGNORE_URLS": [
        "/health/",
        "/health-check/",
        "/favicon.ico",
    ],
}
