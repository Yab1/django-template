# Django Template

Reusable Django application **template** — not a product domain. Clone, rename, and build your service on top.

Includes REST APIs (DRF), JWT auth, Celery, health checks (`/health/`), seed-superuser, and scaffolding tools.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended)
- Docker & Docker Compose (optional; used for deploy / infra)
- PostgreSQL (or use Docker)

## Environment

```bash
cp .env.example .env
# Set DJANGO_SECRET_KEY, DB, and DJANGO_SECRETS_FILE_PATH (e.g. .secrets.yml)
```

## Documentation

Start here: **[docs/index.md](docs/index.md)** (getting started, architecture, REST API, guides).

Contributing: **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## Quick Start

```bash
make help              # all targets
make update            # deps + migrations + hooks
make seed-superuser    # from .secrets.yml / DJANGO_SECRETS_FILE_PATH
make run               # development server
```

Smoke checks after `make run`:

| URL | Purpose |
|-----|---------|
| `GET /health/` | Infra health |
| `GET /docs/` | Swagger (admin session) |
| `POST /api/v1/authentication/token/` | JWT obtain |

Default port comes from `DJANGO_APP_PORT` (see `.env.example`).

## Apps

| App | Role |
|-----|------|
| `core.common` | BaseModel, shared utils, management commands |
| `core.users` | User model and user APIs |
| `core.authentication` | JWT, `/me`, password flows |
| `core.systems` | Health probe |
| `core.api` | Envelope, pagination, URL mount |

## Deployment

Assets under **[deployment/](deployment/)**:

- Docker Compose blue/green (`django_template_*` services)
- [`Jenkinsfile`](deployment/Jenkinsfile), [`entrypoint.sh`](deployment/entrypoint.sh), [`scripts/deploy.sh`](deployment/scripts/deploy.sh)
- Health path used by deploy: `/health/`

See [docs/guides/deployment.md](docs/guides/deployment.md).

## Naming

In-repo identifiers: `django_template` / `django-template` (Compose, Celery queue, image). Rename when you fork into a real product.

## Contact

- **Author**: [Yeabsera](https://github.com/Yab1)

## License

MIT — free to use, modify, and distribute. See [LICENSE](LICENSE).
