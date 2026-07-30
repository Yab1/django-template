# Data Models

This document describes the data model structure in the EHR Practitioner Service.

## Overview

All data models in the service follow FHIR (Fast Healthcare Interoperability Resources) standards to ensure healthcare data interoperability.

## Model Structure

### Base Model

All models inherit from `BaseModel` which provides:
- UUID primary key
- `created_at` timestamp
- `updated_at` timestamp

### FHIR Compliance

Models are designed to be FHIR-compliant:
- Follow FHIR resource structures
- Use FHIR data types
- Include FHIR metadata

## Model Categories

### 1. Core Models

Core domain models:
- `Practitioner` - Healthcare practitioner information
- `PractitionerRole` - Practitioner roles and specialties

### 2. FHIR Data Types

FHIR-compliant data types:
- `CodeableConcept` - Coded concepts
- `Reference` - Resource references
- `Period` - Time periods
- `Identifier` - External identifiers
- And more...

## Modeling Standards

All models must follow the [Django Modeling Standard](../standards/modeling.md) which includes:

- Consistent field naming
- Standard field ordering
- Proper `related_name` patterns
- Complete `help_text` documentation
- Standard Meta configuration

## Model Relationships

Models are related through:
- ForeignKey relationships
- ManyToMany relationships
- Reverse relationships with standardized `related_name`

## Examples

See the [Models Reference](../reference/models.md) for detailed model documentation and examples.

## Related Documentation

- [Django Modeling Standard](../standards/modeling.md)
- [Models Reference](../reference/models.md)

