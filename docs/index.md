# EHR Practitioner Service Documentation

Welcome to the EHR Practitioner Service documentation. This documentation provides comprehensive guides, API references, architecture details, and standards for developers and AI agents.

## Quick Navigation

### Getting Started

- [Getting Started Guide](getting-started.md) - Quick start guide for new developers

### Architecture

- [Architecture Overview](architecture/overview.md) - System architecture overview
- [Multi-Tenant Architecture](architecture/multi-tenant.md) - Multi-tenant architecture details
- [Data Models](architecture/data-models.md) - Data model structure
- [Database Routing](architecture/database-routing.md) - Database routing mechanism
- [Architecture Decision Records](architecture/adr/) - ADRs for major architectural decisions

### APIs

- [GraphQL API](api/graphql/overview.md) - GraphQL API documentation
- [gRPC API](api/grpc/overview.md) - gRPC API documentation

### Guides

- [Development Guide](guides/development.md) - Development setup and workflow
- [Testing Guide](guides/testing.md) - Testing practices and guidelines
- [Deployment Guide](guides/deployment.md) - Deployment procedures
- [Seeding Guide](guides/seeding.md) - Data seeding guide
- [Secrets Management](guides/secrets-management.md) - Secrets management guide

### Standards

- [Django Modeling Standard](standards/modeling.md) - Model creation standards for AI agents
- [Django Fixtures Standard](standards/fixtures.md) - Fixture creation standards for AI agents
- [Django Admin Standard](standards/admin.md) - Admin interface creation standards for AI agents
- [GraphQL Codegen Standard](standards/graphql-codegen.md) - GraphQL codegen configuration standards for AI agents

### Reference

- [Models Reference](reference/models.md) - Models reference documentation
- [Services Reference](reference/services.md) - Services reference documentation
- [Configuration Reference](reference/configuration.md) - Configuration reference
- [Codegen Configuration Reference](reference/codegen-config.md) - Complete reference for codegen configuration options

## Project Overview

EHR Practitioner Service is a Django application built with Strawberry Django for GraphQL APIs, featuring gRPC support, multi-tenant architecture with isolated databases, and FHIR-compliant data models.

### Key Features

- **Strawberry Django**: GraphQL API framework
- **gRPC**: Inter-service communication with mTLS authentication
- **Multi-tenant**: Isolated database per tenant
- **FHIR**: FHIR-compliant data models and types
- **Django Extensions**: Django admin, authentication, and audit logging

## Contributing

When contributing to this project, please:

1. Follow the [Django Modeling Standard](standards/modeling.md) for all model creation
2. Follow the [Django Admin Standard](standards/admin.md) for all admin interface creation
3. Follow the [Django Fixtures Standard](standards/fixtures.md) for all fixture creation
4. Follow the [GraphQL Codegen Standard](standards/graphql-codegen.md) for all GraphQL codegen configuration
5. Update relevant documentation when making changes
6. Ensure all tests pass before submitting changes
7. Follow the established code style and conventions

## Support

For technical questions or contributions, contact:

- **Developer**: [Yeabsera](https://github.com/Yab1)
- **Organization**: [Tilla Health Insurance](https://tillahealth.com/en-US)
