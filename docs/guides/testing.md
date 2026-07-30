# Testing Guide

How we structure and run tests in this template.

## Run tests

```bash
make test
# or
uv run pytest
```

Use `config.django.test` as the settings module (configured in project pytest config when present).

## What to test

Prefer tests that cover **business logic**:

1. **Services** — writes, validation, side effects (hit the database)
2. **Selectors** — query/filter behavior
3. **Models** — only when `clean()`, properties, or methods matter
4. **APIs** — thin smoke tests when useful; mock external I/O

Mock Celery `.delay` / `.apply_async` and third-party HTTP.

## Layout

Match modules with tests under the app:

```text
core/<app>/tests/
  __init__.py
  factories.py          # optional factory_boy
  services/
    test_<service_name>.py
  selectors/
    test_<selector_name>.py
  models/
    test_<model_name>.py
  apis/                 # optional
    test_....py
```

Naming:

- File: `test_<thing>.py`
- Class: `<Thing>Tests`

Example already in tree: `core/authentication/tests/test_login_events.py` (JWT obtain/blacklist + easy-audit events). Note responses may be envelope-wrapped (`result.access`).

## Factories

`factory_boy` and `faker` are available. Prefer factories or services for setup over ad-hoc fixtures when building domain tests.

## Related

- [Django Styleguide](../standards/django-styleguide.md) — testing section
- [Getting Started](../getting-started.md)
