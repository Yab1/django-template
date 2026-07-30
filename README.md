# EHR Django Template

[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/Tilla-Health-Insurance/ehr-django-template)
[![Coverage](https://img.shields.io/badge/coverage-80%25+-green)](https://github.com/Tilla-Health-Insurance/ehr-django-template)

EHR Django Template is a Django application template built with Strawberry Django for GraphQL APIs, featuring gRPC support, multi-tenant architecture with isolated databases, and FHIR-compliant data models. Use this template as a starting point for building EHR microservices.

## Features

- **Strawberry Django**: GraphQL API framework
- **gRPC**: Inter-service communication with mTLS authentication
- **Multi-tenant**: Isolated database per tenant
- **FHIR**: FHIR-compliant data models and types
- **Django Extensions**: Django admin, authentication, and audit logging

## Architecture

This template provides a foundation for building EHR microservices with:

- **Service Provisioning**: Automatically provision services for new tenants via gRPC
- **gRPC Server**: Exposes tenant event endpoints (TenantCreated, TenantUpdated, TenantDeleted) for other services
- **GraphQL API**: Provides flexible data access for frontend applications
- **Database Routing**: Routes database queries based on tenant context for data isolation

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- PostgreSQL (or use Docker)

## Environment Variables

Copy `.env.example` to `.env` and configure the required environment variables for your setup.

## Quick Start

For detailed commands and setup instructions, see the [Makefile](Makefile) - run `make help` to see all available commands.

### Setup

```bash
# Set up everything (dependencies, migrations, submodules, protos, FHIR models)
make update

# Load superusers from secrets file
make seed-superuser

# Start development server
make run
```

## Testing

This template maintains comprehensive test coverage with pytest. All tests are organized by domain (models, services, mutations) following industry best practices.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=core --cov-report=html

# Run specific test file
pytest core/<domain>/tests/

# Run tests in parallel (faster)
pytest -n auto
```

### Test Coverage

- **Target Coverage**: 80% minimum
- **Current Coverage**: See coverage report in `htmlcov/index.html` after running tests
- **Test Organization**:
  - Model tests: `core/*/tests/models/`
  - Service tests: `core/*/tests/services/`
  - Mutation tests: `core/*/tests/mutations/`

For detailed testing documentation, see:

- [Testing Plan](docs/TESTING_PLAN.md)
- [Testing Quick Start](docs/TESTING_QUICK_START.md)

## Data Seeding

The template includes a comprehensive seeding system for generating realistic test data using Faker.

### Quick Start

```bash
# Seed data (example: seed 10 records by default)
make seed-<domain>

# Seed 50 records
make seed-<domain> COUNT=50

# Clear existing data and seed 100 new records
make seed-<domain> COUNT=100 CLEAR=1
```

### Features

- **Realistic Data**: Uses Faker to generate realistic test data
- **Complete Relationships**: Creates related objects with proper relationships
- **FHIR Compliant**: All data follows FHIR standards (when applicable)
- **Configurable**: Control which relationships to create and how many

For detailed seeding documentation, see:

- [Seeding Guide](docs/SEEDING_GUIDE.md)

## Secrets Management

The template includes a secure secrets management system for handling sensitive configuration data like superuser credentials.

### Quick Start

```bash
# Load superusers from YAML secrets file
make seed-superuser

# Update existing superusers
make seed-superuser UPDATE=1
```

### Features

- **YAML-based**: Store secrets in YAML format
- **Environment-driven**: File path configured via `SECRETS_FILE_PATH` env var
- **Secure**: Secrets file never committed to Git
- **Flexible**: Works with Docker, local development, and production

For detailed secrets management documentation, see:

- [Secrets Management Guide](docs/SECRETS_MANAGEMENT_GUIDE.md)

## Deployment

For deployment instructions, see the `docker/` directory:

- **Development**: See `docker/development/README.md`
- **Production**: See `docker/production/README.md`

Both directories include Jenkins deployment setup and detailed documentation.

## Contact

For technical questions or contributions, contact:

- **Developer**: [Yeabsera](https://github.com/Yab1)
- **Organization**: [Tilla Health Insurance](https://tillahealth.com/en-US)

## License

This template is proprietary software. All rights reserved. See the [LICENSE](LICENSE) file for details.
