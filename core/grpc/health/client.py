"""
Health gRPC client.

This module provides a client interface for calling the Health gRPC service.
"""

import logging
from typing import Optional

from core.grpc.utils import create_channel

logger = logging.getLogger(__name__)

try:
    from core.grpc.health.v1 import health_pb2, health_pb2_grpc
except ImportError:
    # Protos not generated yet
    health_pb2 = None
    health_pb2_grpc = None


class HealthClient:
    """Client for interacting with the Health gRPC service."""

    def __init__(self, endpoint: Optional[str] = None):
        """
        Initialize the Health client.

        Args:
            endpoint: gRPC endpoint URL (e.g., "localhost:50054").
            If None, uses settings.SERVICES_GRPC_ENDPOINTS["health"]
        """
        if health_pb2_grpc is None:
            raise ImportError("Health protos not generated. Run 'make proto' to generate them.")

        if endpoint is None:
            from config.settings.grpc import get_grpc_endpoint_for_service

            endpoint = get_grpc_endpoint_for_service("health")
            if endpoint is None:
                raise ValueError("Health gRPC endpoint not configured")

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
                service_name="health",
                roles=[],
                require_tls=require_tls,
            )
            self._stub = health_pb2_grpc.HealthStub(self._channel)

    def check(self, service: str = "") -> health_pb2.HealthCheckResponse:
        """
        Check performs a health check for the service.

        Args:
            service: Name of the service to check (can be empty for overall health)

        Returns:
            HealthCheckResponse with serving status
        """
        if health_pb2 is None:
            raise ImportError("Health protos not generated. Run 'make proto' to generate them.")

        self._ensure_channel()

        request = health_pb2.HealthCheckRequest(service=service)
        response = self._stub.Check(request)
        logger.debug(f"Health check response for service '{service}': {response.status}")
        return response

    def watch(self, service: str = ""):
        """
        Watch performs a streaming health check for the service.

        Args:
            service: Name of the service to watch (can be empty for overall health)

        Yields:
            HealthCheckResponse with serving status updates
        """
        if health_pb2 is None:
            raise ImportError("Health protos not generated. Run 'make proto' to generate them.")

        self._ensure_channel()

        request = health_pb2.HealthCheckRequest(service=service)
        for response in self._stub.Watch(request):
            logger.debug(f"Health watch response for service '{service}': {response.status}")
            yield response

    def close(self):
        """Close the gRPC channel."""
        if self._channel is not None:
            self._channel.close()
            self._channel = None
            self._stub = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
