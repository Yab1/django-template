# Vendor Management Core

Django application template with REST APIs (DRF), JWT auth, Celery, and shared scaffolding tools.

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- PostgreSQL (or use Docker)

## Environment Variables

Copy `.env.example` to `.env` and configure the required environment variables for your setup.

## Quick Start

For detailed commands and setup instructions, see the [Makefile](Makefile) — run `make help` to see all available commands.

**CI (GitHub Actions):** On every push and pull request to `main`, the [CI workflow](.github/workflows/ci.yml) runs dependency audit (`pip-audit`) and lint (`make lint`). Tests are run locally only; run `make test` before pushing. Require this workflow to pass before merging (GitHub branch protection).

### Option A: Run on the host

```bash
# Set up dependencies and migrations
make update

# Git hooks: pre-push blocks direct push to main (use a branch + PR). Installed by make precommit.
# One-time: make install-hooks (or make precommit) so Git uses .githooks/

# Load superusers from secrets file (.secrets.yml / DJANGO_SECRETS_FILE_PATH)
make seed-superuser

# Start development server
make run
```

### Option B: Run with Docker (development)

See **[development/README.md](development/README.md)** if present. From repo root:

```bash
make run
```
