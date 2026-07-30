"""
gRPC service registry utility.

This module provides utilities for automatically registering gRPC servicers
with proper error handling and logging.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def register_servicer(server: Any, service_name: str, servicer_class_name: str | None = None) -> bool:
    """
    Register a gRPC servicer on the server with automatic error handling.

    Args:
        server: The gRPC server instance to register the servicer on
        service_name: Name of the service (e.g., "health", "tenant")
        servicer_class_name: Optional custom servicer class name.
        If None, auto-derives from service_name (e.g., "health" -> "HealthServicer")

    Returns:
        True if registration was successful, False otherwise

    Example:
        register_servicer(server, "health")  # Registers HealthServicer
        register_servicer(server, "tenant")  # Registers TenantServicer
    """
    # Auto-derive servicer class name if not provided
    if servicer_class_name is None:
        servicer_class_name = f"{service_name.capitalize()}Servicer"

    # Derive module paths
    servicer_module = f"core.grpc.{service_name}.service"
    proto_module = f"core.grpc.{service_name}.v1.{service_name}_pb2_grpc"

    try:
        # Import servicer class
        servicer_module_obj = __import__(servicer_module, fromlist=[servicer_class_name])
        servicer_class = getattr(servicer_module_obj, servicer_class_name)

        # Import proto module
        # Use importlib to properly import the module
        import importlib

        try:
            proto_module_obj = importlib.import_module(proto_module)
        except ImportError as e:
            logger.warning(
                f"Failed to import {proto_module}: {e}. Run 'make proto' to generate protos.",
            )
            return False

        # Check if proto module is None (protos not generated)
        if proto_module_obj is None:
            logger.warning(
                f"{servicer_class_name} not available - proto modules are None. Run 'make proto' to generate protos.",
            )
            return False

        # Derive registration function name
        # Try common patterns: add_{ServiceName}Servicer_to_server or add_{ServiceName}ServiceServicer_to_server
        # e.g., "health" -> "add_HealthServicer_to_server" or "add_HealthServiceServicer_to_server"
        service_name_capitalized = service_name.capitalize()

        # Try both common patterns
        possible_names = [
            f"add_{service_name_capitalized}Servicer_to_server",
            f"add_{service_name_capitalized}ServiceServicer_to_server",
        ]

        registration_func = None

        for name in possible_names:
            func = getattr(proto_module_obj, name, None)
            if func is not None and callable(func):
                registration_func = func
                break

        if registration_func is None:
            # Debug: list all available functions in the module
            available_funcs = [
                attr
                for attr in dir(proto_module_obj)
                if "add" in attr and "Servicer" in attr and "server" in attr.lower()
            ]
            logger.warning(
                f"Registration function not found in {proto_module}. Tried: {', '.join(possible_names)}. Available functions: {', '.join(available_funcs) if available_funcs else 'none'}. Skipping {servicer_class_name} registration.",  # noqa: E501
            )
            return False

        # Register the servicer
        registration_func(servicer_class(), server)
        logger.info(f"{servicer_class_name} registered successfully")
        return True

    except ImportError as e:
        logger.warning(
            f"{servicer_class_name} not available - import error: {e}. Run 'make proto' to generate protos.",
        )
        return False
    except Exception as e:
        logger.error(f"Failed to register {servicer_class_name}: {e}", exc_info=True)
        return False
