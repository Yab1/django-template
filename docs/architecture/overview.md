# Architecture Overview

This document provides a high-level overview of the EHR Practitioner Service architecture.

## System Architecture

The EHR Practitioner Service is built using:

- **Django**: Web framework
- **Strawberry Django**: GraphQL API framework
- **gRPC**: Inter-service communication
- **PostgreSQL**: Database (multi-tenant with isolated databases)
- **Celery**: Asynchronous task processing

## Key Components

### 1. Multi-Tenant Architecture

The service implements a multi-tenant architecture where each tenant has:
- Isolated database
- Independent data storage
- Secure data isolation

See [Multi-Tenant Architecture](multi-tenant.md) for details.

### 2. GraphQL API

Strawberry Django provides a GraphQL API for flexible data access.

See [GraphQL API Documentation](../api/graphql/overview.md) for details.

### 3. gRPC Services

gRPC services handle inter-service communication with mTLS authentication.

See [gRPC API Documentation](../api/grpc/overview.md) for details.

### 4. FHIR Compliance

All data models follow FHIR standards for healthcare data interoperability.

See [Data Models](data-models.md) for details.

## Data Flow

```
Client → GraphQL API → Django ORM → Database Router → Tenant Database
                    ↓
                gRPC Services → Other Services
```

## Database Routing

The service uses database routing to ensure tenant data isolation.

See [Database Routing](database-routing.md) for details.

## Security

- Multi-tenant data isolation
- mTLS for gRPC communication
- Keycloak authentication integration
- Audit logging

## Deployment

The service can be deployed using Docker.

See [Deployment Guide](../guides/deployment.md) for details.

