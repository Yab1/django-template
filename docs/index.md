# Django Template Documentation

Reusable Django application template with REST APIs (DRF), JWT auth, Celery, and shared scaffolding. Fork and rename for your product.

## Quick Navigation

### Getting Started

- [Getting Started](getting-started.md) — local setup, seed superuser, run server

### Architecture

- [Architecture Overview](architecture/overview.md) — apps, layers, stack
- [Architecture Decision Records](architecture/adr/) — ADR template and decisions

### APIs

- [REST API Overview](api/rest/overview.md) — auth, users, health, envelope, Postman

### Guides

- [Development](guides/development.md) — workflow and project layout
- [Commands without Make](guides/without-make.md) — raw `uv` / `manage.py` equivalents (Windows-friendly)
- [Testing](guides/testing.md) — pytest layout and practices
- [Deployment](guides/deployment.md) — deploy scripts and health checks
- [Seeding](guides/seeding.md) — `seed-superuser`
- [Secrets Management](guides/secrets-management.md) — `.secrets.yml` and env

### Standards

- [Django Styleguide](standards/django-styleguide.md) — HackSoft layers (Cursor rule)
- [Django Admin Standard](standards/admin.md) — admin conventions (Cursor rule)

### Reference

- [Configuration](reference/configuration.md) — settings layout and env prefixes

## Stack

- **Django 5.2** + **Django REST Framework**
- **SimpleJWT** (access/refresh, blacklist)
- **Celery** + RabbitMQ (optional broker)
- **PostgreSQL**, Redis (cache / channels)
- **drf-spectacular** (OpenAPI at `/schema/`, Swagger at `/docs/`)

## Apps

| App | Role |
|-----|------|
| `core.common` | BaseModel, shared utils, management commands |
| `core.users` | User model, list/update, login events |
| `core.authentication` | JWT obtain/refresh/verify/blacklist, `/me`, password flows |
| `core.systems` | Infrastructure health probe (`/health/`) |
| `core.api` | Envelope, pagination, exception handling, URL mount |

## Contributing

1. Follow the [Django Styleguide](standards/django-styleguide.md) (services / selectors / thin APIs).
2. Follow the [Admin Standard](standards/admin.md) for admin changes.
3. Update docs when behavior or public APIs change.
4. Prefer testing services and selectors; run `make test` / `make lint` before pushing.
