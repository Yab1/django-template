"""
Swagger / OpenAPI 3 configuration (drf-spectacular).

https://drf-spectacular.readthedocs.io/en/latest/settings.html
"""

from config.settings.app import get_app_public_base_url


def _openapi_server_label(base: str) -> str:
    if "localhost" in base or "127.0.0.1" in base:
        return "Local development"
    return "API"


def _openapi_servers() -> list[dict[str, str]]:
    base = get_app_public_base_url()
    return [{"url": base, "description": _openapi_server_label(base)}]


def postprocess_error_responses(result, generator, **kwargs):
    """Inject the standard error envelope into every operation globally."""
    error_ref = {"$ref": "#/components/schemas/ErrorResponse"}
    error_content = {"application/json": {"schema": error_ref}}

    error_resp = {
        "description": (
            "Error response (400 validation, 401 unauthorized, 403 forbidden, 404 not found, 429 throttled)."
        ),
        "content": error_content,
    }

    for _path, methods in result.get("paths", {}).items():
        for _method, operation in methods.items():
            if not isinstance(operation, dict) or "responses" not in operation:
                continue
            operation["responses"].setdefault("4XX", error_resp)

    schemas = result.setdefault("components", {}).setdefault("schemas", {})
    schemas.setdefault(
        "ErrorMeta",
        {
            "type": "object",
            "properties": {"version": {"type": "string"}},
            "required": ["version"],
        },
    )
    schemas.setdefault(
        "ProblemDetail",
        {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": [
                        "validation-error",
                        "unauthorized",
                        "forbidden",
                        "not-found",
                        "throttled",
                        "internal-server-error",
                        "error",
                    ],
                },
                "title": {"type": "string"},
                "status": {"type": "integer"},
                "detail": {"type": "string"},
                "instance": {"type": "string"},
                "errors": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
            },
            "required": ["type", "title", "status", "detail"],
        },
    )
    schemas.setdefault(
        "ErrorResponse",
        {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["error"]},
                "result": {"$ref": "#/components/schemas/ProblemDetail"},
                "meta": {"$ref": "#/components/schemas/ErrorMeta"},
                "message": {"type": "string"},
            },
            "required": ["status", "result", "meta", "message"],
        },
    )

    return result


SPECTACULAR_SETTINGS = {
    "TITLE": "Vendor Management API",
    "DESCRIPTION": "REST API for Vendor Management Core.",
    "VERSION": "0.0.1",
    "TOS": "https://www.google.com/policies/terms/",
    "CONTACT": {
        "name": "Vendor Management Team",
        "url": "https://tillahealth.com/en-US",
        "email": "yeabsera.dev@gmail.com",
    },
    "SERVERS": _openapi_servers(),
    "EXTERNAL_DOCS": {
        "url": "https://tillahealth.com/en-US",
        "description": "External documentation",
    },
    "SERVE_PUBLIC": True,
    "SERVE_INCLUDE_SCHEMA": False,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": False,
        "filter": True,
        "tagsSorter": "alpha",
        "docExpansion": "none",
        "defaultModelsExpandDepth": 1,
    },
    "ENUM_NAME_OVERRIDES": {
        "SuccessStatusEnum": [("success", "success")],
        "CacheStatusEnum": [("ok", "ok"), ("error", "error")],
        "MinioStatusEnum": [("ok", "ok"), ("error", "error"), ("not_configured", "not_configured")],
    },
    "REDOC_UI_SETTINGS": {},
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "config.settings.swagger.postprocess_error_responses",
    ],
}
