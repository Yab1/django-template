"""
Health gRPC service implementation.

This module implements the Health gRPC servicer using the standard gRPC health checking protocol.
"""

import logging

import grpc

try:
    from core.grpc.health.v1 import health_pb2, health_pb2_grpc
except ImportError:
    # Protos not generated yet
    health_pb2 = None
    health_pb2_grpc = None

logger = logging.getLogger(__name__)


class HealthServicer(health_pb2_grpc.HealthServicer if health_pb2_grpc else object):
    """
    Implements the Health gRPC service.

    Provides endpoints for:
    - Check: Performs a health check for the service
    - Watch: Performs a streaming health check for the service
    """

    def __init__(self):
        if health_pb2_grpc is None:
            raise ImportError("Health protos not generated. Run 'make proto' to generate them.")
        logger.debug("HealthServicer initialized")

    def Check(self, request, context):
        """
        Check performs a health check for the service.

        Args:
            request: HealthCheckRequest containing optional service name
            context: gRPC servicer context

        Returns:
            HealthCheckResponse with SERVING status
        """
        if health_pb2 is None:
            context.set_code(grpc.StatusCode.UNIMPLEMENTED)
            context.set_details("Health protos not generated")
            return None

        # Return SERVING status for the requested service (or default if empty)
        service_name = request.service if request.service else "default"
        logger.debug(f"Health check requested for service: {service_name}")

        return health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.ServingStatus.SERVING,
        )

    def Watch(self, request, context):
        """
        Watch performs a streaming health check for the service.

        Args:
            request: HealthCheckRequest containing optional service name
            context: gRPC servicer context

        Yields:
            HealthCheckResponse with SERVING status
        """
        if health_pb2 is None:
            context.set_code(grpc.StatusCode.UNIMPLEMENTED)
            context.set_details("Health protos not generated")
            return

        service_name = request.service if request.service else "default"
        logger.debug(f"Health watch requested for service: {service_name}")

        # Stream SERVING status
        # In a real implementation, you might want to check actual service health
        # and stream updates when status changes
        yield health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.ServingStatus.SERVING,
        )
