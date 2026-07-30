"""
gRPC server registration hook for django-grpc.

This module defines `grpc_hook(server)` which django-grpc calls to add
servicers to the running gRPC server.
"""

from core.grpc.registry import register_servicer


def grpc_hook(server) -> None:
    """
    Register all gRPC servicers on the provided server instance.

    To add a new service, simply add it to the SERVICES list below.
    """
    # List of services to register
    # Each service will be automatically registered with error handling
    services_to_register = [
        "health",
        "tenant",
    ]

    # Register each service
    for service_name in services_to_register:
        register_servicer(server, service_name)
