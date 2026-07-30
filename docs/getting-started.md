# Getting Started

This guide will help you get started with the EHR Practitioner Service.

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- PostgreSQL (or use Docker)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ehr-practitioner-service
```

### 2. Set Up Environment

```bash
# Copy environment file
cp .env.example .env

# Configure environment variables
# Edit .env with your settings
```

### 3. Install Dependencies

```bash
# Using Makefile (recommended)
make update

# Or manually
pip install -e ".[dev]"
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Superuser

```bash
make seed-superuser
```

### 6. Start Development Server

```bash
make run
```

The service will be available at `http://localhost:8000`

## Next Steps

- Read the [Development Guide](guides/development.md) for detailed development setup
- Check the [Architecture Overview](architecture/overview.md) to understand the system
- Review the [API Documentation](api/graphql/overview.md) for API usage
- Follow the [Modeling Standards](standards/modeling.md) when creating new models

## Common Commands

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=core --cov-report=html

# Start development server
make run

# Run migrations
python manage.py migrate

# Create migrations
python manage.py makemigrations
```

