"""
Tenant gRPC service implementation.

This module implements the TenantService gRPC servicer.
"""

import logging

try:
    from core.grpc.tenant.v1 import tenant_pb2, tenant_pb2_grpc
except ImportError:
    # Protos not generated yet
    tenant_pb2 = None
    tenant_pb2_grpc = None

logger = logging.getLogger(__name__)


class TenantServicer(tenant_pb2_grpc.TenantServiceServicer if tenant_pb2_grpc else object):
    """
    Implements the TenantService gRPC service.

    Provides endpoints for:
    - GetTenant: Retrieves a single tenant by ID
    """

    def __init__(self):
        if tenant_pb2_grpc is None:
            raise ImportError("Tenant protos not generated. Run 'make proto' to generate them.")
        logger.debug("TenantServicer initialized")
