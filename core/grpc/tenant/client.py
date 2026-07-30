"""
Tenant gRPC client.

This module provides a client interface for calling the Tenant gRPC service.
"""

import logging
from typing import Optional

from core.grpc.utils import create_channel

logger = logging.getLogger(__name__)

try:
    from core.grpc.tenant.v1 import tenant_pb2, tenant_pb2_grpc
except ImportError:
    # Protos not generated yet
    tenant_pb2 = None
    tenant_pb2_grpc = None


class TenantClient:
    """Client for interacting with the Tenant gRPC service."""

    def __init__(self, endpoint: Optional[str] = None):
        """
        Initialize the Tenant client.

        Args:
            endpoint: gRPC endpoint URL (e.g., "localhost:50029").
            If None, uses settings.SERVICES_GRPC_ENDPOINTS["tenant"]
        """
        if tenant_pb2_grpc is None:
            raise ImportError("Tenant protos not generated. Run 'make proto' to generate them.")

        if endpoint is None:
            from config.settings.grpc import get_grpc_endpoint_for_service

            endpoint = get_grpc_endpoint_for_service("tenant")
            if endpoint is None:
                raise ValueError("Tenant gRPC endpoint not configured")

        self.endpoint = endpoint
        self._channel = None
        self._stub = None

    def _ensure_channel(self):
        """Ensure the gRPC channel is created."""
        if self._channel is None:
            # Check if we should use TLS based on environment
            # In development, allow insecure connections if TLS isn't properly configured
            from django.conf import settings

            # Use TLS only if explicitly required AND properly configured
            require_tls = getattr(settings, "GRPC_REQUIRE_TLS", False)

            # If TLS is not required, we'll use insecure channel if TLS config is incomplete
            self._channel = create_channel(
                self.endpoint,
                service_name="tenant",
                roles=[],
                require_tls=require_tls,
            )
            self._stub = tenant_pb2_grpc.TenantServiceStub(self._channel)
