"""
Swagger / OpenAPI 3 configuration (drf-spectacular).

https://drf-spectacular.readthedocs.io/en/latest/settings.html
"""

from config.env import env
from config.settings.app import APP_VERSION, get_app_public_base_url


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


SWAGGER_ENABLED = env.bool("DJANGO_SWAGGER_ENABLED", default=True)

_swagger_tos = env.str("DJANGO_SWAGGER_TOS", default="").strip()
_swagger_external_docs_url = env.str("DJANGO_SWAGGER_EXTERNAL_DOCS_URL", default="").strip()
_swagger_external_docs_desc = env.str("DJANGO_SWAGGER_EXTERNAL_DOCS_DESC", default="").strip()

SPECTACULAR_SETTINGS = {
    "TITLE": env.str("DJANGO_SWAGGER_TITLE", default="Django Template API"),
    "DESCRIPTION": env.str("DJANGO_SWAGGER_DESCRIPTION", default="REST API for Django Template."),
    "VERSION": env.str("DJANGO_SWAGGER_VERSION", default=APP_VERSION),
    "CONTACT": {
        "name": env.str("DJANGO_SWAGGER_CONTACT_NAME", default="Django Template"),
        "url": env.str("DJANGO_SWAGGER_CONTACT_URL", default=""),
        "email": env.str("DJANGO_SWAGGER_CONTACT_EMAIL", default=""),
    },
    "SERVERS": _openapi_servers(),
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
        "CacheStatusEnum": [("ok", "ok"), ("error", "error"), ("not_configured", "not_configured")],
        "MinioStatusEnum": [("ok", "ok"), ("error", "error"), ("not_configured", "not_configured")],
    },
    "REDOC_UI_SETTINGS": {},
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
        "config.settings.swagger.postprocess_error_responses",
    ],
}

if _swagger_tos:
    SPECTACULAR_SETTINGS["TOS"] = _swagger_tos
if _swagger_external_docs_url:
    SPECTACULAR_SETTINGS["EXTERNAL_DOCS"] = {
        "url": _swagger_external_docs_url,
        "description": _swagger_external_docs_desc,
    }
