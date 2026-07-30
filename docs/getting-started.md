# Getting Started

Local setup for Django Template.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or an equivalent virtualenv
- Docker & Docker Compose (optional, for Postgres/Redis/RabbitMQ)
- PostgreSQL (or use Docker)

## 1. Clone and configure env

```bash
cp .env.example .env
# Set at least DJANGO_SECRET_KEY, database, and DJANGO_SECRETS_FILE_PATH
```

Point secrets at a local YAML file (gitignored):

```bash
# .env
DJANGO_SECRETS_FILE_PATH=.secrets.yml
```

See [Secrets Management](guides/secrets-management.md) for the YAML shape.

## 2. Install and migrate

```bash
make update
```

This installs dependencies and runs migrations. Use `make help` for all targets.

## 3. Seed a superuser

```bash
make seed-superuser
# Update existing accounts:
make seed-superuser UPDATE=1
```

Username defaults to the email local-part (e.g. `yeabsera.dev` for `yeabsera.dev@gmail.com`). Password must pass Django validators (including HIBP).

## 4. Run the server

```bash
make run
```

Default local URL uses `DJANGO_APP_DOMAIN` / `DJANGO_APP_PORT` (often `http://localhost:7000`).

## Smoke checks

| URL | Purpose |
|-----|---------|
| `GET /health/` | Infra health (DB, cache, RabbitMQ, MinIO when configured) |
| `GET /docs/` | Swagger UI (admin session auth) |
| `GET /schema/` | OpenAPI schema |
| `POST /api/v1/authentication/token/` | Obtain JWT |

Versioned REST APIs live under `/api/v1/`. Details: [REST API Overview](api/rest/overview.md).

## Next

- [Development guide](guides/development.md)
- [Commands without Make](guides/without-make.md) — if `make` is unavailable
- [Postman collections](../postman/) under `postman/<app>/`
- [Architecture overview](architecture/overview.md)
