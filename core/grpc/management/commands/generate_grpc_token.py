"""
Django management command to generate gRPC JWT tokens for testing.

Usage:
    python manage.py generate_grpc_token
    python manage.py generate_grpc_token --service-name ehr_patient --roles admin,reader
    python manage.py generate_grpc_token --ttl 3600  # 1 hour
"""

import datetime

import jwt
from django.conf import settings
from django.core.management.base import BaseCommand


def generate_service_token(
    ttl_seconds: int = 300,
    service_name: str | None = None,
    roles: list[str] | None = None,
    metadata: dict | None = None,
) -> str:
    """
    Generate a JWT service token for inter-service authentication.

    This function is used by:
    - Management command (generate_grpc_token for manual testing)
    - gRPC clients (automatic token generation in create_channel)

    Args:
        ttl_seconds: Token expiration time in seconds (default: 5 minutes)
        service_name: Service identifier (default: from settings.SERVICE_NAME)
        roles: List of roles/permissions (default: from settings.SERVICE_ROLES)
        metadata: Additional custom claims to include

    Returns:
        Encoded JWT token string

    Note:
        Uses TILLA_PAY_CLIENT_SECRET if available (more secure), otherwise falls back
        to SERVICE_TOKEN_SECRET for backward compatibility.
    """
    import logging

    logger = logging.getLogger(__name__)

    now = datetime.datetime.now(datetime.timezone.utc)

    if service_name is None:
        service_name = getattr(settings, "SERVICE_NAME", "unknown-service")
    if roles is None:
        roles = getattr(settings, "SERVICE_ROLES", [])

    # Get client_id and client_secret from settings (stored in env)
    # Use client_secret for signing - each application has its own secret (more secure!)
    try:
        from config.settings.tilla_pay import TILLA_PAY_CLIENT_ID, TILLA_PAY_CLIENT_SECRET

        client_id = TILLA_PAY_CLIENT_ID
        client_secret = TILLA_PAY_CLIENT_SECRET
    except ImportError:
        # Fallback to getattr if import fails
        client_id = getattr(settings, "TILLA_PAY_CLIENT_ID", None)
        client_secret = getattr(settings, "TILLA_PAY_CLIENT_SECRET", None)

    # Warn if client_id is missing (but still allow token generation for backward compatibility)
    if not client_id:
        logger.warning(
            "TILLA_PAY_CLIENT_ID not set - client_id will not be included in JWT token. This may cause authentication failures on the server.",  # noqa: E501
        )

    payload = {
        # Standard JWT claims
        "iss": getattr(settings, "SERVICE_TOKEN_ISSUER", "tilla-id"),
        "aud": getattr(settings, "SERVICE_TOKEN_AUDIENCE", "tilla-services"),
        "sub": service_name,  # Service identity (for backward compatibility)
        "iat": int(now.timestamp()),
        "exp": int((now + datetime.timedelta(seconds=ttl_seconds)).timestamp()),
        # Custom claims for service authorization
        "service": service_name,  # Redundant with sub, but explicit
        "roles": roles,  # Service roles/permissions
        # Client ID claim - used to identify RegisteredApplication
        # Only include if client_id is available
        **({"client_id": client_id} if client_id else {}),
    }

    # Add custom metadata if provided
    if metadata:
        payload.update(metadata)

    # Use client_secret for signing (same as REST API approach!)
    # Each application signs with its own secret - more secure than shared SERVICE_TOKEN_SECRET
    if not client_secret:
        # Fallback to SERVICE_TOKEN_SECRET if client_secret not available (for backward compatibility)
        secret = getattr(settings, "SERVICE_TOKEN_SECRET", getattr(settings, "SECRET_KEY", "CHANGE_ME_NOW"))
        logger.warning("TILLA_PAY_CLIENT_SECRET not set, falling back to SERVICE_TOKEN_SECRET")
    else:
        secret = client_secret

    return jwt.encode(payload, secret, algorithm="HS256")


class Command(BaseCommand):
    help = "Generate a JWT token for gRPC service authentication (for testing)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--service-name",
            type=str,
            default=None,
            help="Service name (default: from settings.SERVICE_NAME)",
        )
        parser.add_argument(
            "--roles",
            type=str,
            default=None,
            help="Comma-separated list of roles (default: from settings.SERVICE_ROLES)",
        )
        parser.add_argument(
            "--ttl",
            type=int,
            default=3600,
            help="Token TTL in seconds (default: 3600 = 1 hour)",
        )
        parser.add_argument(
            "--format",
            type=str,
            choices=["token", "header", "curl"],
            default="token",
            help="Output format: token (just token), header (Authorization header), curl (curl command)",
        )

    def handle(self, *args, **options):
        from django.conf import settings

        service_name = options["service_name"]
        roles_str = options["roles"]
        roles = [r.strip() for r in roles_str.split(",")] if roles_str else None
        ttl_seconds = options["ttl"]
        output_format = options["format"]

        # Generate token using the token generation function
        token = generate_service_token(
            ttl_seconds=ttl_seconds,
            service_name=service_name,
            roles=roles,
        )

        # Get settings for display
        actual_service_name = service_name or getattr(settings, "SERVICE_NAME", "ehr_patient")
        actual_roles = roles if roles is not None else getattr(settings, "SERVICE_ROLES", [])
        audience = getattr(settings, "SERVICE_TOKEN_AUDIENCE", "tilla-services")
        issuer = getattr(settings, "SERVICE_TOKEN_ISSUER", "tilla-id")

        # Output based on format
        if output_format == "token":
            self.stdout.write(self.style.SUCCESS(f"\nToken:\n{token}\n"))
        elif output_format == "header":
            self.stdout.write(self.style.SUCCESS(f"\nAuthorization Header:\nBearer {token}\n"))
        elif output_format == "curl":
            self.stdout.write(
                self.style.SUCCESS(
                    f'\ncurl -X POST -H "Authorization: Bearer {token}" \\\n  -H "Content-Type: application/json" \\\n  http://localhost:50054\n',
                ),
            )

        # Show token details
        self.stdout.write(self.style.SUCCESS("\nToken Details:"))
        self.stdout.write(f"  Service: {actual_service_name}")
        self.stdout.write(f"  Roles: {', '.join(actual_roles) if actual_roles else 'none'}")
        self.stdout.write(f"  Expires in: {ttl_seconds} seconds ({ttl_seconds // 3600}h {(ttl_seconds % 3600) // 60}m)")
        self.stdout.write(f"  Issuer: {issuer}")
        self.stdout.write(f"  Audience: {audience}\n")

        # Usage instructions for Postman
        self.stdout.write(self.style.WARNING("\nFor Postman:"))
        self.stdout.write("  1. Go to your gRPC request")
        self.stdout.write("  2. Click on 'Metadata' tab")
        self.stdout.write(f"  3. Add header: Key: 'authorization', Value: 'Bearer {token}'")
        self.stdout.write("")
