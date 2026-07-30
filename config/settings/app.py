"""
App-specific Django settings.

All custom settings that use DJANGO_*-prefixed environment variables
should live here. Base settings (config/django/base.py) import this module.
"""

# pyright: reportArgumentType=false

from uuid import UUID

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

REFERENCE_ID_PLATFORM_PREFIX = env("DJANGO_REFERENCE_ID_PLATFORM_PREFIX", default="HB")

# FHIR Identifier.system for facility-issued patient MRNs (assigning authority URL).
PATIENT_MRN_IDENTIFIER_SYSTEM = env.str(
    "DJANGO_PATIENT_MRN_IDENTIFIER_SYSTEM",
    default=f"{APP_DOMAIN}/fhir/sid/patient-mrn",
)
# Zero-padded decimal width for MRN values (common EMR practice: 7–10 digits).
PATIENT_MRN_NUMERIC_WIDTH = env.int("DJANGO_PATIENT_MRN_NUMERIC_WIDTH", default=9)
# First numeric MRN issued for a new sequence row (default 0). Ignored once the
# sequence row exists — adjust the DB row or reset if you must reseed live data.
# int(...) narrows django-environ's loose typing for basedpyright.
PATIENT_MRN_SEQUENCE_START: int = int(env.int("DJANGO_PATIENT_MRN_SEQUENCE_START", default=0))
if PATIENT_MRN_SEQUENCE_START < 0:
    msg = "DJANGO_PATIENT_MRN_SEQUENCE_START must be >= 0"
    raise ValueError(msg)

# Workflow activity system user (Temporal + POST /workflows/activities/execute/).
# Must match core/systems/fixtures/workflow_system_user.json when using fixtures.
_workflow_system_user_id_raw = env.str("DJANGO_WORKFLOW_SYSTEM_USER_ID", default="").strip()  # pyright: ignore[reportOptionalMemberAccess]
WORKFLOW_SYSTEM_USER_ID: UUID | None = UUID(_workflow_system_user_id_raw) if _workflow_system_user_id_raw else None
WORKFLOW_SYSTEM_USERNAME = env.str("DJANGO_WORKFLOW_SYSTEM_USERNAME", default="workflow.system").strip()  # pyright: ignore[reportOptionalMemberAccess]
