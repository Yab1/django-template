# Seeding Guide

This guide covers data seeding for the EHR Practitioner Service.

## Overview

The service includes a comprehensive seeding system for generating realistic test data using Faker.

## Quick Start

```bash
# Seed practitioners (default: 10 records)
make seed-practitioners

# Seed with custom count
make seed-practitioners COUNT=50

# Clear existing data and seed
make seed-practitioners COUNT=100 CLEAR=1
```

## Features

- **Realistic Data**: Uses Faker to generate realistic test data
- **Complete Relationships**: Creates related objects with proper relationships
- **FHIR Compliant**: All data follows FHIR standards
- **Configurable**: Control which relationships to create and how many

## Seeding Commands

### Practitioners

```bash
make seed-practitioners COUNT=10
```

### Practitioner Roles

```bash
make seed-practitioner-roles COUNT=10
```

## Custom Seeding

You can create custom seeding scripts:

```python
from core.practitioners.factories import PractitionerFactory

# Create 10 practitioners
practitioners = PractitionerFactory.create_batch(10)
```

## Related Documentation

- [Development Guide](development.md)
- [Testing Guide](testing.md)

