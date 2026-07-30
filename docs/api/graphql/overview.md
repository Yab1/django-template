# GraphQL API Overview

This document provides an overview of the GraphQL API in the EHR Practitioner Service.

## Overview

The service uses Strawberry Django to provide a GraphQL API for flexible data access.

## Features

- Type-safe GraphQL schema
- Automatic schema generation from Django models
- Query and mutation support
- Filtering and pagination
- Authentication via Keycloak

## Schema

The GraphQL schema is automatically generated from Django models and includes:
- Types for all models
- Queries for data retrieval
- Mutations for data modification
- Filters and pagination

## Authentication

GraphQL API uses Keycloak for authentication:
- JWT tokens required
- User context available in resolvers
- Role-based access control

## Examples

See [GraphQL Examples](examples.md) for usage examples.

## Related Documentation

- [GraphQL Queries](queries.md)
- [GraphQL Mutations](mutations.md)
- [GraphQL Examples](examples.md)

