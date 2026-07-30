"""
gRPC configuration for Patient Service.
"""

import os
from typing import Optional

from config.env import env

try:
    import grpc  # type: ignore
except Exception:  # pragma: no cover - grpc may not be installed in some envs
    grpc = None  # type: ignore

# TLS configuration
GRPC_TLS_ENABLED = env.bool("GRPC_TLS_ENABLED", default=False)

# TLS certificate files
GRPC_TLS_CERT_FILE = env.str("GRPC_TLS_CERT_FILE", default=None)
GRPC_TLS_KEY_FILE = env.str("GRPC_TLS_KEY_FILE", default=None)
GRPC_TLS_CA_FILE = env.str("GRPC_TLS_CA_FILE", default=None)

# Optional client certs for outbound mTLS
GRPC_CLIENT_CERT_FILE = env.str("GRPC_CLIENT_CERT_FILE", default=None)
GRPC_CLIENT_KEY_FILE = env.str("GRPC_CLIENT_KEY_FILE", default=None)

# gRPC Auth interceptor configuration
GRPC_AUTH_ENABLED = env.bool("GRPC_AUTH_ENABLED", default=True)


def _build_server_credentials() -> Optional[list[dict]]:
    """
    Build server credentials configuration for django-grpc.

    django-grpc expects credentials as a list of dictionaries with file paths,
    not grpc.ServerCredentials objects. It will build the credentials internally.

    Env vars:
    - GRPC_TLS_ENABLED: "true" to enable TLS (default: False)
    - GRPC_TLS_CERT_FILE: path to server cert (PEM)
    - GRPC_TLS_KEY_FILE: path to server private key (PEM)
    - GRPC_TLS_CA_FILE: optional path to CA cert for client auth (PEM)

    Returns:
        List of credential dicts with 'private_key' and 'certificate_chain' keys,
        or None if TLS is not configured
    """
    if grpc is None:
        return None

    # Disable TLS if explicitly disabled
    if not GRPC_TLS_ENABLED:
        return None

    cert_file = GRPC_TLS_CERT_FILE
    key_file = GRPC_TLS_KEY_FILE
    ca_file = GRPC_TLS_CA_FILE

    if not cert_file or not key_file:
        return None

    # Verify files exist before returning config
    try:
        if not os.path.exists(cert_file):
            return None
        if not os.path.exists(key_file):
            return None
        if ca_file and not os.path.exists(ca_file):
            # CA file is optional, so just log warning if specified but missing
            pass
    except Exception:
        return None

    # django-grpc expects a list of credential dictionaries with file paths
    # It will read the files and build ServerCredentials internally
    return [
        {
            "private_key": key_file,
            "certificate_chain": cert_file,
        },
    ]

    # Note: django-grpc doesn't directly support CA file or require_client_auth
    # in the config dict format. Those would need to be handled differently
    # if needed (possibly through gRPC options or a custom server setup).


GRPCSERVER = {
    # Register gRPC servicers via this hook function
    "servicers": ["core.grpc.server.grpc_hook"],
    # Server interceptors: auth, logging, etc.
    # Note: Auth interceptor is instantiated at runtime to support method roles
    # Set GRPC_AUTH_ENABLED=false to disable authentication for development/testing
    "interceptors": [
        "core.grpc.interceptors.auth.ServiceAuthInterceptor",
    ]
    if GRPC_AUTH_ENABLED
    else [],
    "maximum_concurrent_rpcs": None,
    "options": [("grpc.max_receive_message_length", 1024 * 1024 * 100)],
    # TLS credentials: set from env. If None, runs insecure (dev only)
    # Note: If GRPC_TLS_CA_FILE is provided, django-grpc may use it for client cert verification
    "credentials": _build_server_credentials(),
    # Run in sync mode by default; switch to True to enable ASGI-aware async
    "async": False,
    # Enable if you want server reflection for tooling
    "reflection": False,
}

# gRPC server configuration
GRPC_SERVER_ADDRESS = env.str("GRPC_SERVER_ADDRESS", default="0.0.0.0:50023")
GRPC_SERVER_MAX_WORKERS = env.int("GRPC_SERVER_MAX_WORKERS", default=10)

# gRPC client endpoints for other services
SERVICES_GRPC_ENDPOINTS = {
    "ehr_tenant": os.getenv("GRPC_ENDPOINT_EHR_TENANT", "localhost:50051"),
    # "ehr_practitioner": os.getenv("GRPC_ENDPOINT_EHR_PRACTITIONER", "localhost:50052"),
    # "ehr_hospital": os.getenv("GRPC_ENDPOINT_EHR_HOSPITAL", "localhost:50053"),
    "ehr_patient": os.getenv("GRPC_ENDPOINT_EHR_PATIENT", "localhost:50054"),
    # "ehr_clinical": os.getenv("GRPC_ENDPOINT_EHR_CLINICAL", "localhost:50054"),
    # "ehr_appointment": os.getenv("GRPC_ENDPOINT_EHR_APPOINTMENT", "localhost:50055"),
}


def get_grpc_endpoint_for_service(slug: str) -> str | None:
    """
    Get gRPC endpoint for a service by slug.

    Args:
        slug: Service slug

    Returns:
        Endpoint string or None if not found
    """
    return SERVICES_GRPC_ENDPOINTS.get(slug)


# Service-to-service auth token settings (used by interceptor and clients)
SERVICE_TOKEN_SECRET = env.str(
    "SERVICE_TOKEN_SECRET",
    default=env.str("SDA_TOKEN_SECRET_KEY", default=env.str("SECRET_KEY", default="CHANGE_ME_NOW")),
)
SERVICE_TOKEN_AUDIENCE = env.str("SERVICE_TOKEN_AUDIENCE", default="tilla-services")
SERVICE_TOKEN_ISSUER = env.str("SERVICE_TOKEN_ISSUER", default="tilla-id")
SERVICE_TOKEN_LEEWAY_SECONDS = env.int("SERVICE_TOKEN_LEEWAY_SECONDS", default=30)

# Service identity and roles
SERVICE_NAME = env.str("SERVICE_NAME", default="ehr_patient")  # Current service identifier
SERVICE_ROLES = env.list("SERVICE_ROLES", default=[])
# SERVICE_ROLES example: "admin,reader,writer" becomes ["admin", "reader", "writer"]


# Optional: Method-level role requirements
# Format: {"method_name": ["required_role1", "required_role2"]}
SERVICE_METHOD_ROLES = {
    # Example:
    # "CreateCheckout": ["admin", "writer"],
    # "GetInvoice": ["admin", "reader", "writer"],
}
