"""Shared OpenAPI response maps for product endpoints.

``OPENAPI_ERRORS`` is the write that can return 409: validation, permission,
missing row, and conflict (domain or idempotency-key reuse).
``OPENAPI_VALIDATION_ERRORS`` is that map without 409, for a write that only
raises ``ValidationError``. Do not rebuild either map in a view.
A read lists only the statuses it returns (``403``, ``404``).
"""

OPENAPI_ERRORS = {
    400: None,
    403: None,
    404: None,
    409: None,
}

OPENAPI_VALIDATION_ERRORS = {code: OPENAPI_ERRORS[code] for code in (400, 403, 404)}
