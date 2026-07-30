# Services Reference

This document provides a reference for all services in the EHR Practitioner Service.

## Service Pattern

Services encapsulate business logic and provide a clean interface for operations.

## Practitioner Service

**Location**: `core.practitioners.services.PractitionerService`

### Methods

- `create()` - Create a new practitioner
- `update()` - Update an existing practitioner
- `delete()` - Delete a practitioner
- `get_by_id()` - Retrieve practitioner by ID
- `list()` - List practitioners with filtering

## Service Standards

- Services handle business logic
- Services validate input
- Services handle errors gracefully
- Services return domain objects

## Related Documentation

- [Development Guide](../guides/development.md)
- [Models Reference](models.md)

