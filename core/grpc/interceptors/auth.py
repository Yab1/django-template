"""
Service-to-service authentication interceptor for gRPC servers.

This interceptor validates:
1. JWT token presence and validity
2. Service identity (sub/service claim)
3. Token expiration
4. Optional: Service roles/permissions
5. mTLS certificate verification (cross-verify with JWT service identity)
"""

import logging
from typing import Callable, Optional

import grpc
import jwt
from django.conf import settings

logger = logging.getLogger(__name__)

# Context key to store verified service identity
_SERVICE_IDENTITY_KEY = "service_identity"


def _get_bearer_token_from_metadata(metadata: Optional[tuple]) -> Optional[str]:
    """Extract Bearer token from gRPC metadata."""
    if not metadata:
        logger.debug("No metadata provided")
        return None

    # Debug: Log all metadata keys to help diagnose issues
    logger.info(f"Metadata keys received: {[key for key, _ in metadata] if metadata else 'empty'}")

    for key, value in metadata:
        logger.info(f"Checking metadata key: '{key}' (type: {type(value).__name__})")
        if key.lower() == "authorization" and isinstance(value, (str, bytes)):
            val = value.decode() if isinstance(value, (bytes, bytearray)) else value
            logger.info(f"Found authorization header, value starts with: {val[:30] if len(val) > 30 else val}")
            if val.lower().startswith("bearer "):
                token = val[7:].strip()
                logger.info(
                    f"Successfully extracted token (first 30 chars): {token[:30] if len(token) > 30 else token}",
                )
                return token
            logger.warning(f"Authorization header doesn't start with 'bearer ': {val[:50]}")

    logger.warning("No valid Bearer token found in metadata")
    return None


def _decode_and_validate_token(token: str) -> dict:
    """
    Decode and validate JWT service token.

    Note: This is for inter-service authentication where tokens are signed with
    SERVICE_TOKEN_SECRET. For application tokens (signed with client_secret),
    use the RegisteredApplication lookup approach in tilla-pay.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload with claims

    Raises:
        jwt.ExpiredSignatureError: Token has expired
        jwt.InvalidTokenError: Token is invalid or malformed
        ValueError: Required claims are missing
    """
    secret = getattr(settings, "SERVICE_TOKEN_SECRET", getattr(settings, "SECRET_KEY", "CHANGE_ME_NOW"))
    audience = getattr(settings, "SERVICE_TOKEN_AUDIENCE", None)
    issuer = getattr(settings, "SERVICE_TOKEN_ISSUER", None)
    leeway = getattr(settings, "SERVICE_TOKEN_LEEWAY_SECONDS", 30)

    options = {"require": ["exp", "sub"]}  # Require expiration and subject (service name)
    kwargs = {"algorithms": ["HS256"], "options": options, "leeway": leeway}
    if audience:
        kwargs["audience"] = audience
    if issuer:
        kwargs["issuer"] = issuer

    # Decode and validate token - raises jwt exceptions on failure
    logger.debug(
        f"Decoding token with secret (first 10 chars): {secret[:10] if secret else 'None'}..., audience: {audience}, issuer: {issuer}",  # noqa: E501
    )
    payload = jwt.decode(token, secret, **kwargs)
    logger.debug(f"Token decoded successfully. Claims: {list(payload.keys())}")

    # Validate service identity (sub or service claim)
    service_name = payload.get("sub") or payload.get("service")
    if not service_name:
        raise ValueError("Token missing service identity (sub or service claim)")

    return payload


def _extract_peer_certificate_cn(context: grpc.ServicerContext) -> Optional[str]:
    """
    Extract Common Name (CN) from the peer's mTLS certificate.

    Args:
        context: gRPC servicer context

    Returns:
        Certificate CN string or None if not available
    """
    try:
        # Access peer certificate information from context
        auth_context = context.auth_context()
        if not auth_context:
            return None

        # Extract certificate from auth context
        # The key format may vary based on gRPC implementation
        cert_key = None
        for key in auth_context:
            if isinstance(key, bytes):
                key_str = key.decode("utf-8", errors="ignore").lower()
                if "x509" in key_str or "cert" in key_str:
                    cert_key = key
                    break

        if not cert_key:
            # Try common key names
            for key_name in [b"x509_common_name", b"x509_cert", b"peer_cert"]:
                if key_name in auth_context:
                    cert_key = key_name
                    break

        if cert_key:
            cert_data = auth_context.get(cert_key)
            if cert_data:
                # Extract CN from certificate (format varies)
                if isinstance(cert_data, bytes):
                    cert_str = cert_data.decode("utf-8", errors="ignore")
                    # Try to extract CN from certificate string
                    # This is a simplified extraction - adjust based on your cert format
                    for line in cert_str.split("\n"):
                        if "CN=" in line or "Common Name:" in line:
                            # Extract CN value
                            parts = line.split("CN=") if "CN=" in line else line.split("Common Name:")
                            if len(parts) > 1:
                                return parts[1].strip().split()[0].strip(",").strip('"').strip("'")

        # Alternative: Use peer identity if available
        peer_identity = getattr(context, "peer_identity", None)
        if peer_identity:
            return str(peer_identity)

        return None
    except Exception as e:
        logger.debug(f"Failed to extract peer certificate CN: {e}")
        return None


def _verify_certificate_jwt_match(
    cert_cn: Optional[str],
    jwt_service_name: str,
    require_cert_match: bool = True,
) -> bool:
    """
    Verify that certificate CN matches JWT service identity.

    Args:
        cert_cn: Certificate Common Name (can be None)
        jwt_service_name: Service name from JWT token
        require_cert_match: If True, requires certificate match when certificate is available

    Returns:
        True if match or certificate not required, False if mismatch
    """
    if not require_cert_match:
        return True

    # If certificate is not available (development mode), allow it
    if not cert_cn:
        logger.debug(f"Certificate CN not available, skipping certificate verification for service: {jwt_service_name}")
        return True

    # Normalize both values for comparison (case-insensitive, strip whitespace)
    cert_cn_normalized = cert_cn.lower().strip()
    jwt_service_normalized = jwt_service_name.lower().strip()

    # Exact match
    if cert_cn_normalized == jwt_service_normalized:
        return True

    # Certificate CN might include additional info (e.g., "service-name/instance-id")
    # Check if JWT service name matches the first part
    if "/" in cert_cn_normalized:
        cert_base = cert_cn_normalized.split("/")[0]
        if cert_base == jwt_service_normalized:
            return True

    logger.warning(
        f"Certificate-JWT mismatch: cert CN='{cert_cn}', JWT service='{jwt_service_name}'. Rejecting request for security.",  # noqa: E501
    )
    return False


def _validate_service_authorization(payload: dict, required_roles: Optional[list[str]] = None) -> None:
    """
    Validate service has required roles/permissions.

    Args:
        payload: Decoded JWT payload
        required_roles: List of required roles (if None, only validates token, not roles)

    Raises:
        PermissionError: Service doesn't have required roles
    """
    if required_roles is None:
        return  # No role validation required

    service_roles = payload.get("roles", [])
    if not isinstance(service_roles, list):
        service_roles = []

    # Check if service has any of the required roles
    if not any(role in service_roles for role in required_roles):
        service_name = payload.get("sub") or payload.get("service", "unknown")
        raise PermissionError(
            f"Service '{service_name}' does not have required roles: {required_roles}. Service has roles: {service_roles}",  # noqa: E501
        )


def _wrap_unary_unary(
    handler: grpc.RpcMethodHandler,
    required_roles: Optional[list[str]] = None,
) -> grpc.RpcMethodHandler:
    """
    Wrap unary-unary RPC handler with auth validation.

    Args:
        handler: Original RPC method handler
        required_roles: Optional list of required roles for this method
    """

    def new_behavior(request, context: grpc.ServicerContext):
        try:
            # Extract token from metadata
            token = _get_bearer_token_from_metadata(context.invocation_metadata())
            if not token:
                logger.error("No token found in metadata")
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Missing bearer token")

            logger.info(f"Token extracted, validating token (length: {len(token)})")
            # Decode and validate token (includes expiration, signature, claims)
            try:
                payload = _decode_and_validate_token(token)
                logger.info(f"Token validated successfully. Service: {payload.get('service') or payload.get('sub')}")
            except Exception as e:
                logger.error(f"Token validation failed: {type(e).__name__}: {str(e)}")
                raise

            # Extract service identity from JWT
            service_identity = payload.get("sub") or payload.get("service")
            if not service_identity:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token missing service identity")

            # Validate service has required roles (if any)
            _validate_service_authorization(payload, required_roles)

            # mTLS certificate verification: Cross-verify certificate CN with JWT service identity
            require_cert_match = getattr(settings, "GRPC_REQUIRE_CERT_JWT_MATCH", True)
            cert_cn = _extract_peer_certificate_cn(context)
            if not _verify_certificate_jwt_match(cert_cn, service_identity, require_cert_match):
                context.abort(
                    grpc.StatusCode.UNAUTHENTICATED,
                    "Certificate-JWT mismatch: certificate CN does not match JWT service identity",
                )

            # Store verified service identity in context for use in servicer methods
            # Using setattr to attach to context object (common pattern for gRPC)
            setattr(context, _SERVICE_IDENTITY_KEY, service_identity)

            # Also store full payload for potential future use (e.g., roles)
            setattr(context, f"{_SERVICE_IDENTITY_KEY}_payload", payload)

            logger.debug(f"Verified service identity: {service_identity} (cert CN: {cert_cn})")
            context.set_code(grpc.StatusCode.OK)  # Ensure OK status

        except jwt.ExpiredSignatureError:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token expired")
        except jwt.InvalidTokenError as e:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, f"Invalid token: {str(e)}")
        except ValueError as e:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, f"Token validation error: {str(e)}")
        except PermissionError as e:
            context.abort(grpc.StatusCode.PERMISSION_DENIED, f"Authorization failed: {str(e)}")
        except Exception as e:
            logger.exception(f"Authentication error: {e}")
            context.abort(grpc.StatusCode.INTERNAL, f"Authentication error: {str(e)}")

        # Call the actual handler
        return handler.unary_unary(request, context)

    return grpc.unary_unary_rpc_method_handler(
        new_behavior,
        request_deserializer=handler.request_deserializer,
        response_serializer=handler.response_serializer,
    )


def _wrap_other(handler: grpc.RpcMethodHandler) -> grpc.RpcMethodHandler:
    """For brevity, protect only unary-unary methods now. Extend as needed."""
    return handler


class ServiceAuthInterceptor(grpc.ServerInterceptor):
    """
    Validates Authorization: Bearer <JWT> for incoming gRPC calls.

    This interceptor ensures:
    - JWT token is present and valid
    - Service identity is verified
    - Token hasn't expired
    - Optional: Service has required permissions/roles

    Works with mTLS: TLS encryption + JWT authentication provides
    defense in depth (transport security + application-level auth).
    """

    def __init__(self, require_roles: Optional[dict[str, list[str]]] = None):
        """
        Initialize the auth interceptor.

        Args:
            require_roles: Optional dict mapping method names to required roles.
            Example: {"GetTenant": ["admin"], "GetPractitioner": ["reader", "admin"]}
        """
        self.require_roles = require_roles or {}

    def intercept_service(self, continuation: Callable, handler_call_details: grpc.HandlerCallDetails):
        handler = continuation(handler_call_details)
        if handler is None:
            return None

        # Get method name from handler call details
        method_name = handler_call_details.method if hasattr(handler_call_details, "method") else None
        required_roles = None
        if method_name and method_name in self.require_roles:
            required_roles = self.require_roles[method_name]

        if handler.unary_unary:
            return _wrap_unary_unary(handler, required_roles=required_roles)
        return _wrap_other(handler)
