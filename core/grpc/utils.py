"""
Shared utilities for gRPC clients and servers.
"""

import logging
import os
from typing import Optional, Sequence, Tuple

import grpc
from django.conf import settings

logger = logging.getLogger(__name__)

# Import service identity extraction from auth module
try:
    from core.grpc.interceptors.auth import _SERVICE_IDENTITY_KEY
except ImportError:
    # Fallback if not available
    _SERVICE_IDENTITY_KEY = "service_identity"


def _build_client_ssl_credentials() -> grpc.ChannelCredentials | None:
    """
    Build SSL credentials for gRPC client from settings.

    Returns None if TLS is not properly configured (for development fallback).
    """
    root_certificates = None
    private_key = None
    certificate_chain = None

    ca_file = getattr(settings, "GRPC_TLS_CA_FILE", None) or None
    if ca_file:
        try:
            # Handle relative paths from project root (same as client cert/key)
            if not os.path.isabs(ca_file):
                project_root = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                )
                ca_file = os.path.join(project_root, ca_file)

            if os.path.exists(ca_file):
                with open(ca_file, "rb") as f:
                    root_certificates = f.read()
            else:
                # File doesn't exist - log warning but don't fail
                logger.warning(f"TLS CA certificate file not found: {ca_file}. Falling back to insecure channel.")
                root_certificates = None
        except Exception as e:
            logger.warning(f"Failed to load TLS CA certificate from {ca_file}: {e}. Falling back to insecure channel.")
            root_certificates = None

    client_cert = getattr(settings, "GRPC_CLIENT_CERT_FILE", None) or None
    client_key = getattr(settings, "GRPC_CLIENT_KEY_FILE", None) or None
    if client_cert and client_key:
        try:
            # Handle relative paths from project root
            if not os.path.isabs(client_cert):
                project_root = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                )
                client_cert = os.path.join(project_root, client_cert)
            if not os.path.isabs(client_key):
                project_root = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                )
                client_key = os.path.join(project_root, client_key)

            if os.path.exists(client_key) and os.path.exists(client_cert):
                with open(client_key, "rb") as f:
                    private_key = f.read()
                with open(client_cert, "rb") as f:
                    certificate_chain = f.read()
            else:
                # Files don't exist - log warning
                if not os.path.exists(client_key):
                    logger.warning(f"TLS client key file not found: {client_key}")
                if not os.path.exists(client_cert):
                    logger.warning(f"TLS client cert file not found: {client_cert}")
        except Exception as e:
            logger.warning(f"Failed to load TLS client certificates: {e}")
            private_key = None
            certificate_chain = None

    # For client connections to work properly, we need:
    # 1. CA certificate (root_certificates) to verify the server's certificate, OR
    # 2. At minimum, client cert+key for mTLS, but we still need CA for verification

    # Without CA certificate, we can't verify the server, so return None
    # This allows fallback to insecure channel for development
    if not root_certificates:
        # No CA certificate means we can't verify server - don't use TLS
        return None

    # We have CA certificate, so we can verify the server
    # Client cert+key are optional (for mTLS)
    return grpc.ssl_channel_credentials(
        root_certificates=root_certificates,
        private_key=private_key,
        certificate_chain=certificate_chain,
    )


class _MetadataInjector(grpc.UnaryUnaryClientInterceptor):
    """Client interceptor to inject metadata into gRPC calls."""

    def __init__(self, metadata: Sequence[Tuple[str, str]]):
        self._metadata = list(metadata)

    def intercept_unary_unary(self, continuation, client_call_details, request):
        md = [] if client_call_details.metadata is None else list(client_call_details.metadata)
        md.extend(self._metadata)
        client_call_details = client_call_details._replace(metadata=tuple(md))
        return continuation(client_call_details, request)


def create_channel(
    target: str,
    service_name: str | None = None,
    roles: list[str] | None = None,
    require_tls: bool = False,
) -> grpc.Channel:
    """
    Create a gRPC channel with automatic mTLS and service auth.

    Args:
        target: gRPC endpoint (e.g., "localhost:50029")
        service_name: Service identifier for JWT (default: from settings)
        roles: Service roles for JWT (default: from settings)
        require_tls: If True, requires TLS configuration or raises error

    Returns:
        gRPC Channel with TLS and JWT authentication

    Raises:
        ValueError: If require_tls=True but TLS is not configured
    """
    # Check if we should force insecure mode (for local development/testing)
    force_insecure = getattr(settings, "GRPC_FORCE_INSECURE", False)

    # For localhost connections, allow insecure by default unless explicitly required
    is_localhost = target.startswith(("localhost:", "127.0.0.1:"))

    # Check if TLS is properly configured (files exist and credentials can be built)
    credentials = _build_client_ssl_credentials()
    has_tls = credentials is not None and not force_insecure

    if require_tls and not has_tls and not force_insecure:
        raise ValueError(
            "TLS is required but not configured. Set GRPC_TLS_CA_FILE and GRPC_CLIENT_CERT_FILE/GRPC_CLIENT_KEY_FILE environment variables.",  # noqa: E501
        )

    # Connection strategy:
    # 1. If force_insecure is set, always use insecure
    # 2. If TLS credentials are available (certs exist), use TLS (server likely requires it)
    # 3. For localhost without TLS config, use insecure (pure dev mode)
    # 4. For non-localhost without TLS, use insecure (will fail if server requires TLS)
    if force_insecure:
        # Force insecure mode (for testing)
        logger.info(f"Using insecure gRPC channel for {target} (GRPC_FORCE_INSECURE=True)")
        base_channel = grpc.insecure_channel(target)
    elif has_tls:
        # TLS credentials available - use them (server likely requires TLS)
        # This works for both localhost and remote connections
        logger.debug(f"Using secure gRPC channel for {target} (TLS credentials configured)")
        base_channel = grpc.secure_channel(target, credentials)
    else:
        # No TLS config - use insecure (development mode)
        # Note: This will fail if the server requires TLS
        if is_localhost:
            logger.debug(f"Using insecure gRPC channel for {target} (localhost without TLS config)")
        else:
            logger.warning(f"Using insecure gRPC channel for {target} (no TLS config, may fail if server requires TLS)")
        base_channel = grpc.insecure_channel(target)

    # Generate JWT token with service identity and roles
    # Import from management command to avoid duplication
    from core.grpc.management.commands.generate_grpc_token import generate_service_token

    token = generate_service_token(service_name=service_name, roles=roles)

    # Inject JWT in Authorization header
    interceptor = _MetadataInjector([("authorization", f"Bearer {token}")])
    return grpc.intercept_channel(base_channel, interceptor)


def get_service_identity(context: grpc.ServicerContext) -> Optional[str]:
    """
    Extract verified service identity from gRPC context.

    This identity was verified by the ServiceAuthInterceptor and includes
    both mTLS certificate and JWT validation.

    Args:
        context: gRPC servicer context

    Returns:
        Service identity string (e.g., "tilla_idir") or None if not available
    """
    return getattr(context, _SERVICE_IDENTITY_KEY, None)


def get_service_identity_payload(context: grpc.ServicerContext) -> Optional[dict]:
    """
    Extract full JWT payload from gRPC context.

    Args:
        context: gRPC servicer context

    Returns:
        JWT payload dict or None if not available
    """
    return getattr(context, f"{_SERVICE_IDENTITY_KEY}_payload", None)
