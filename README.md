# EHR Backend

EHR Backend is a Django application with REST APIs

## Prerequisites

- Python 3.12+
- Docker & Docker Compose
- PostgreSQL (or use Docker)

## Environment Variables

Copy `.env.example` to `.env` and configure the required environment variables for your setup.

## Quick Start

For detailed commands and setup instructions, see the [Makefile](Makefile) - run `make help` to see all available commands.

**CI (GitHub Actions):** On every push and pull request to `main`, the [CI workflow](.github/workflows/ci.yml) runs dependency audit (`pip-audit`) and lint (`make lint`). Tests are run locally only; run `make test` before pushing. Require this workflow to pass before merging (GitHub branch protection).

### Option A: Run on the host

```bash
# Set up everything (dependencies, migrations, submodules, protos, FHIR models)
make update

# Git hooks: pre-push blocks direct push to main (use a branch + PR). Installed by make precommit.
# One-time: make install-hooks (or make precommit) so Git uses .githooks/

# Load superusers from secrets file
make seed-superuser

# Start development server
make run
```

### Option B: Run with Docker (development)

Django + PostgreSQL in Docker. Uses your `.env` (see **[development/README.md](development/README.md)**). From repo root:

```bash
docker compose -f development/docker-compose.yml up --build
```

Ports and DB settings come from `.env`. Code in `core/` and `config/` is mounted so runserver picks up changes.

## Contributing

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for setup, onboarding checklist, and how to open a PR (branch from `main`, run `make lint` and `make test`, no direct push to `main`).

## Documentation

Project docs (style guide, code organization, architecture, features) live in **[docs/](docs/)**. Start at [docs/README.md](docs/README.md) for the index and where to add new docs.

## Deployment

Deployment assets live in **[deployment/](deployment/)**:

- **[Dockerfile](deployment/Dockerfile)** and **[docker-compose.yml](deployment/docker-compose.yml)** for containerized runs
- **[Jenkinsfile](deployment/Jenkinsfile)** for CI/CD
- **[entrypoint.sh](deployment/entrypoint.sh)** and **[scripts/](deployment/scripts/)** for build and deploy (e.g. `deploy.sh`, `orchestrate.sh`, `config.sh`)
- **[gunicorn.config.py](deployment/gunicorn.config.py)** for production WSGI server config

See the [deployment Makefile](deployment/Makefile) for deployment-related commands.

## Contact

For technical questions or contributions, contact:

- **Developer**: [Yeabsera](https://github.com/Yab1)
- **Organization**: [Tilla Health Insurance](https://tillahealth.com/en-US)

## License

This software is proprietary. All rights reserved. See the [LICENSE](LICENSE) file for details.
