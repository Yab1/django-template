# gRPC Examples

This document provides practical examples of using the gRPC API.

## Python Client Example

```python
import grpc
from ehr_protos.tenant import tenant_pb2, tenant_pb2_grpc

# Create channel with mTLS
channel = grpc.secure_channel(
    'localhost:50051',
    grpc.ssl_channel_credentials(
        root_certificates=open('ca.crt').read(),
        private_key=open('client.key').read(),
        certificate_chain=open('client.crt').read()
    )
)

# Create stub
stub = tenant_pb2_grpc.TenantServiceStub(channel)

# Call TenantCreated
request = tenant_pb2.TenantCreatedRequest(
    tenant_id="12345",
    tenant_name="Example Tenant"
)
response = stub.TenantCreated(request)
print(response.success)
```

## Health Check Example

```python
from ehr_protos.health import health_pb2, health_pb2_grpc

# Create health stub
health_stub = health_pb2_grpc.HealthServiceStub(channel)

# Ping
ping_request = health_pb2.PingRequest()
ping_response = health_stub.Ping(ping_request)
print(ping_response.message)  # "pong"
```

## Related Documentation

- [gRPC Overview](overview.md)
- [gRPC Endpoints](endpoints.md)

