# Database Routing

This document describes the database routing mechanism used for multi-tenant data isolation.

## Overview

The EHR Practitioner Service uses a custom database router to route database queries to the correct tenant database based on the current tenant context.

## How It Works

### 1. Tenant Context Detection

The router detects the tenant context from:
- Request headers (HTTP requests)
- gRPC metadata (gRPC requests)
- Authentication tokens

### 2. Database Selection

Once the tenant is identified, the router:
- Selects the appropriate database for that tenant
- Routes all queries to that database
- Ensures no cross-tenant data access

### 3. Query Routing

All Django ORM queries are automatically routed:
- Model queries
- Migrations
- Management commands

## Configuration

Database routing is configured in Django settings:

```python
DATABASE_ROUTERS = ['django_tenant_db_router.router.TenantDatabaseRouter']
```

## Router Implementation

The router implements Django's database routing interface:
- `db_for_read()` - Selects database for read operations
- `db_for_write()` - Selects database for write operations
- `allow_relation()` - Determines if relations are allowed
- `allow_migrate()` - Determines if migrations should run

## Tenant Database Naming

Tenant databases follow a naming convention:
- Pattern: `{tenant_prefix}_{tenant_id}`
- Example: `ehr_tenant_12345`

## Security

The router ensures:
- Complete data isolation
- No accidental cross-tenant queries
- Secure tenant context validation

## Related Documentation

- [Multi-Tenant Architecture](multi-tenant.md)
- [Configuration Reference](../reference/configuration.md)

