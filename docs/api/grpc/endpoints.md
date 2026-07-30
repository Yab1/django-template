# gRPC Endpoints

This document describes the available gRPC endpoints.

## Tenant Service

### TenantCreated

Called when a new tenant is created.

```protobuf
rpc TenantCreated(TenantCreatedRequest) returns (TenantCreatedResponse);
```

### TenantUpdated

Called when a tenant is updated.

```protobuf
rpc TenantUpdated(TenantUpdatedRequest) returns (TenantUpdatedResponse);
```

### TenantDeleted

Called when a tenant is deleted.

```protobuf
rpc TenantDeleted(TenantDeletedRequest) returns (TenantDeletedResponse);
```

## Health Service

### Ping

Basic health check endpoint.

```protobuf
rpc Ping(PingRequest) returns (PingResponse);
```

### Health

Detailed health status endpoint.

```protobuf
rpc Health(HealthRequest) returns (HealthResponse);
```

## Related Documentation

- [gRPC Overview](overview.md)
- [gRPC Examples](examples.md)

