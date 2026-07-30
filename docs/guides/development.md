# Development Guide

Day-to-day development for Django Template.

## Tooling

- **Package manager:** `uv` (see `pyproject.toml` / `uv.lock`)
- **Commands:** root `Makefile` — run `make help`
- **Settings module:** `config.django.base` (override via `DJANGO_SETTINGS_MODULE`)

Common targets:

```bash
make update    # deps + migrations
make run       # development server
make test      # pytest
make lint      # project lint target
make seed-superuser
```

## Project layout

```text
core/<app>/
  models/       # or models.py
  services/     # writes
  selectors/    # reads
  apis/         # thin DRF views
  serializers/
  urls.py
  admin.py
config/
  django/       # Django settings
  settings/     # Celery, JWT, CORS, …
postman/<app>/  # Postman collections
```

Wire new app URLs in [`core/api/urls.py`](../../core/api/urls.py) and register the app in `LOCAL_APPS` (`config/django/base.py`).

## Style

Follow the HackSoft-inspired layers:

- Writes → **services** (`<entity>_<action>`, keyword-only args)
- Reads → **selectors**
- APIs → validate → call service/selector → serialize (no domain logic in views)

Cursor rule: [`.cursor/rules/django-styleguide.mdc`](../../.cursor/rules/django-styleguide.mdc)  
Doc pointer: [Django Styleguide](../standards/django-styleguide.md)

Admin: [`.cursor/rules/admin-standard.mdc`](../../.cursor/rules/admin-standard.mdc)

## Scaffolding

Management helpers under `core/common/management/commands/`:

- `create_app` — new Django app scaffold
- `scaffold_standard_api` / serializers — generate REST boilerplate
- `load_superusers` — seed from secrets YAML
- `generate_postman_collection` — optional generator for Postman

Command docs: `core/common/management/commands/docs/`.

## Git hooks

```bash
make install-hooks   # or make precommit
```

Pre-push may block direct pushes to `main` (use a branch + PR).

## Useful URLs (local)

- App: `http://localhost:7000/` (port from env)
- Health: `/health/`
- Swagger: `/docs/`
- API: `/api/v1/`
