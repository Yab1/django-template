# Configuration Reference

Where settings and environment variables live in this template.

## Layout

```text
config/
  env.py                 # django-environ Env
  django/
    base.py              # main Django settings; imports config.settings.*
    local.py             # optional local overrides
    production.py        # production overlays
    test.py              # pytest / test settings
  settings/
    celery.py
    cors.py
    simple_jwt.py
    rest_framework.py
    swagger.py
    logging.py
    channels.py
    …                    # other integrations
```

Everything needed at runtime should be reachable from `base.py` (or production importing base). Feature flags / optional integrations typically read env and no-op when unset.

## Environment prefixes

| Prefix / name | Use |
|---------------|-----|
| `DJANGO_*` | Django-related (e.g. `DJANGO_DEBUG`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_SECRETS_FILE_PATH`, `DJANGO_JWT_*`) |
| `CELERY_*` | Celery / broker |
| `SENTRY_DSN` | Error tracking (when configured) |
| `MINIO_*` / storage backends | Object storage |

Do not invent a second secrets path env var — use **`DJANGO_SECRETS_FILE_PATH`**.

## Local files

| File | Role |
|------|------|
| `.env` | Local overrides (gitignored) |
| `.env.example` | Documented keys for new clones |
| `.secrets.yml` | Superuser bootstrap YAML (gitignored) |

Copy `.env.example` → `.env`, then set secrets path and database URLs.

## Notable app settings

- `AUTH_USER_MODEL` = `users.User`
- `CELERY_BEAT_SCHEDULE` starts empty — add product tasks when needed
- API mounted at `/api/v1/` via `config/urls.py` → `core.api.urls`
- Health at `/health/` (outside versioned API)

## Related

- [Getting Started](../getting-started.md)
- [Secrets Management](../guides/secrets-management.md)
- [Architecture Overview](../architecture/overview.md)
