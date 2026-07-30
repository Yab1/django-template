# Commands without Make

Use this guide when `make` is unavailable (common on Windows) or you prefer running tools directly.

## Prerequisite: activate the venv

```bash
uv sync --all-extras          # once (creates .venv/)
```

Then activate (do this in every new terminal):

| Shell | Command |
|-------|---------|
| Linux / macOS | `source .venv/bin/activate` |
| Windows cmd | `.venv\Scripts\activate.bat` |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |

After that, commands are plain `python`, `pytest`, `ruff`, `celery` — **no `uv run`**.

Optional: if you skip activate, prefix with `uv run` (e.g. `uv run python manage.py migrate`). Tables below assume the venv is active.

Default port for `runserver` here is `6000` (same as Makefile `DJANGO_PORT`).

---

## First-time setup

| Make | What it does | Without make |
|------|----------------|--------------|
| `make install` | Install deps | `uv sync --all-extras` (add `uv lock` first if `uv.lock` missing) |
| `make migrate` | Apply DB migrations | `python manage.py migrate` |
| `make install-hooks` | Point Git at `.githooks/` | `git config core.hooksPath .githooks` |
| `make precommit` | Hooks path + pre-commit | `git config core.hooksPath .githooks` then `pre-commit install-hooks` |
| `make update` | install + migrate + precommit | Run the rows above in order |

`scripts/install.sh` needs Bash. On Windows, use `uv sync --all-extras` instead.

---

## Day-to-day Django

| Make | What it does | Without make |
|------|----------------|--------------|
| `make run` | Dev server on port 6000 | `python manage.py runserver 6000` |
| `make shell` | Django shell | `python manage.py shell` |
| `make django-check` | System checks | `python manage.py check` |
| `make migrations` | Create migrations | `python manage.py makemigrations` |
| `make migrate` | Apply migrations | `python manage.py migrate` |
| `make makemigrate` | Create + apply | `python manage.py makemigrations` then `python manage.py migrate` |
| `make dry-migrate` | Dry-run makemigrations | `python manage.py makemigrations --dry-run` |
| `make flush` | Wipe DB data | `python manage.py flush --noinput` |
| `make superuser` | Interactive createsuperuser | `python manage.py createsuperuser` |
| `make collectstatic` | Collect static files | `python manage.py collectstatic --noinput` |
| `make seed-superuser` | Load from secrets YAML | `python manage.py load_superusers` |
| `make seed-superuser UPDATE=1` | Update existing | `python manage.py load_superusers --update` |
| `make create-app APP=foo` | Scaffold app | `python manage.py create_app foo` |
| `make create-app APP=foo REGISTER=1` | Scaffold + register | `python manage.py create_app foo --register` |

Secrets: set `DJANGO_SECRETS_FILE_PATH` in `.env` (see [Secrets Management](secrets-management.md)).

---

## Lint / format / audit

Install with `uv sync --all-extras` so `ruff`, `pre-commit`, and `pip-audit` are on `PATH` inside the venv.

| Make | What it does | Without make |
|------|----------------|--------------|
| `make format` | Ruff format | `ruff format .` |
| `make lint` | Format + ruff + hooks | `ruff format .` then `ruff check . --fix` then optional `pre-commit run --all-files` |
| `make audit` | Dependency CVE scan | `pip-audit` |
| `make sync-rules` | Sync Cursor rules → Codex/Claude | `python scripts/sync_from_cursor_rules.py` |

---

## Tests

| Make | What it does | Without make |
|------|----------------|--------------|
| `make test` | All tests | `pytest` |
| `make test-cov` | Coverage (term) | `pytest --cov=core --cov-report=term-missing` |
| `make test-html` | HTML coverage | `pytest --cov=core --cov-report=html --cov-report=term-missing` |
| `make test-xml` | XML coverage (CI) | `pytest --cov=core --cov-report=xml --cov-report=term-missing` |
| `make test-fast` | No coverage | `pytest --no-cov` |
| `make test-app APP=users` | One app | `pytest core/users/tests/ --cov=core.users --cov-report=term-missing` |
| `make test-models` | Model tests | `pytest core/*/tests/models/` |
| `make test-services` | Service tests | `pytest core/*/tests/services/` |
| `make test-unit` | `@pytest.mark.unit` | `pytest -m unit` |
| `make test-integration` | `@pytest.mark.integration` | `pytest -m integration` |
| `make test-create-db` | Recreate test DB | `pytest --create-db` |

`make test-mutations` / `test-queries` are GraphQL leftovers — ignore unless you add those test dirs.

---

## Celery

| Make | What it does | Without make |
|------|----------------|--------------|
| `make celery` | Worker | `celery -A config.settings.celery worker --loglevel=info --pool=solo` |
| `make celery-beat` | Beat | `celery -A config.settings.celery beat --loglevel=info` |
| `make celery-all` | Worker + beat | `celery -A config.settings.celery worker --loglevel=info --pool=solo --beat` |

---

## Honcho multi-process (`make dev`)

| Make | What it does | Without make |
|------|----------------|--------------|
| `make dev` / `dev-all` | Django + Celery + Beat via Honcho | `honcho start` |
| `make dev-web` | Web only | `honcho start web` |
| `make dev-celery` | Worker only | `honcho start celery` |
| `make dev-celery-beat` | Beat only | `honcho start celery-beat` |
| `make dev-stop` | Kill honcho (Unix `pkill`) | Stop the terminal / Task Manager; on Unix: `pkill -f "honcho start"` |

`dev-stop` is Unix-oriented. On Windows, stop processes manually or use separate terminals for server + celery + beat.

---

## Postman generator

```bash
python manage.py generate_postman_collection <app> --resource <resource>
# optional: --category, --output, --name, --dry-run, --merge, …
```

Example: `python manage.py generate_postman_collection users`

---

## Deploy / Docker orchestration

These shell scripts expect a Unix-like environment (Git Bash, WSL, or Linux CI):

| Make | Without make |
|------|----------------|
| `make start` | `./deployment/scripts/orchestrate.sh start` |
| `make stop` | `./deployment/scripts/orchestrate.sh stop` |
| `make restart` | `./deployment/scripts/orchestrate.sh restart` |
| `make status` | `./deployment/scripts/orchestrate.sh status` |
| `make deploy` | `./deployment/scripts/deploy.sh` |

---

## Optional / niche

| Make | Without make |
|------|----------------|
| `make rebase-main` (`BR=dev`) | `git fetch origin main` then `git rebase origin/main` (on the expected branch) |
| `make clean-migrations` | Delete `core/**/migrations/*.py` except `__init__.py` |
| `make submodule*` | `git submodule sync` / `update --init --recursive` or `./scripts/submodule-init.sh` |
| `make graphify-*` | `python -m graphify …` (see `makefiles/Makefile.graphify.mk`) |
| `make open-coverage` | Open `htmlcov/index.html` (`start htmlcov\index.html` on Windows) |

---

## Minimal Windows / no-make bootstrap

```powershell
Copy-Item .env.example .env
# Edit .env — set DJANGO_SECRET_KEY, DB, DJANGO_SECRETS_FILE_PATH

uv sync --all-extras
.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py load_superusers
python manage.py runserver 6000
```

Then hit `http://127.0.0.1:6000/health/`.

---

## Related

- [Getting Started](../getting-started.md)
- [Development](development.md)
- Root [`Makefile`](../../Makefile) and [`makefiles/`](../../makefiles/) — source of truth when this page drifts
