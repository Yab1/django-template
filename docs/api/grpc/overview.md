# gRPC API Overview

This document provides an overview of the gRPC API in the EHR Practitioner Service.

## Overview

The service uses gRPC for inter-service communication with mTLS authentication.

## Features

- Type-safe gRPC services
- mTLS authentication
- Tenant event handling
- Health check service

## Services

### Tenant Service

Handles tenant lifecycle events:
- `TenantCreated` - New tenant creation
- `TenantUpdated` - Tenant updates
- `TenantDeleted` - Tenant deletion

### Health Service

Provides health check endpoints:
- `Ping` - Basic health check
- `Health` - Detailed health status

## Authentication

gRPC uses mTLS (mutual TLS) for authentication:
- Client certificates required
- Server certificate validation
- Secure inter-service communication

## Protocol Buffers

Service definitions are in Protocol Buffer format:
- Located in `protos/ehr_protos/`
- Auto-generated Python code
- Version controlled

## Related Documentation

- [gRPC Endpoints](endpoints.md)
- [gRPC Examples](examples.md)

