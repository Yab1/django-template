# Multi-Tenant Architecture

This document describes the multi-tenant architecture implementation in the EHR Practitioner Service.

## Overview

The EHR Practitioner Service implements a multi-tenant architecture where each tenant has an isolated database. This ensures complete data separation and security between tenants.

## Architecture Details

### Tenant Isolation

- **Database per Tenant**: Each tenant has its own PostgreSQL database
- **Dynamic Routing**: Database routing is handled dynamically based on tenant context
- **Automatic Provisioning**: New tenant databases are provisioned automatically via gRPC

### Tenant Context

The tenant context is determined from:
- Request headers
- gRPC metadata
- Authentication tokens

### Database Router

The service uses a custom database router (`django-tenant-db-router`) that:
- Routes queries to the correct tenant database
- Handles tenant context management
- Ensures data isolation

## Tenant Lifecycle

### 1. Tenant Creation

When a new tenant is created:
1. gRPC event `TenantCreated` is received
2. New database is provisioned
3. Migrations are run on the new database
4. Initial data is seeded (if needed)

### 2. Tenant Updates

When a tenant is updated:
1. gRPC event `TenantUpdated` is received
2. Database configuration is updated
3. Migrations are applied if needed

### 3. Tenant Deletion

When a tenant is deleted:
1. gRPC event `TenantDeleted` is received
2. Database is backed up (if configured)
3. Database is dropped

## Configuration

Tenant configuration is managed through:
- Environment variables
- Database settings
- gRPC service configuration

## Security Considerations

- Complete data isolation between tenants
- No cross-tenant data access
- Secure tenant context validation
- Audit logging per tenant

## Related Documentation

- [Database Routing](database-routing.md)
- [gRPC API](../api/grpc/overview.md)
- [Configuration Reference](../reference/configuration.md)

