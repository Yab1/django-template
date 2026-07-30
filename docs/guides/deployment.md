# Deployment Guide

Production-oriented deploy notes for this template.

## Layout

```text
deployment/
  scripts/deploy.sh      # blue-green Docker deploy
  entrypoint.sh          # migrate, collectstatic, then gunicorn
  gunicorn.config.py
  nginx/                 # active upstream config for proxy
  Jenkinsfile            # CI/CD pipeline (when used)
```

## Health check

Deploy waits on:

```text
GET /health/
```

Not under `/api/v1/`. Returns 200 when probes are ok / `not_configured`, 503 when unhealthy.

See [REST API Overview](../api/rest/overview.md) for probe details.

## Blue-green (Docker)

[`deployment/scripts/deploy.sh`](../../deployment/scripts/deploy.sh):

1. Bring up the inactive slot
2. Wait for migrations/collectstatic marker, then HTTP health
3. Switch nginx upstream
4. Stop the old slot

Proxy / slot names use the `django_template_*` prefix in this template.

## Runtime expectations

- Set production env (see [Configuration](../reference/configuration.md) and `.env.example`)
- `DJANGO_DEBUG=False`, strong `DJANGO_SECRET_KEY` / JWT signing key
- Secrets file available to the container if you run `load_superusers` in ops (usually seed once, not every deploy)
- Celery worker + beat if you schedule tasks (`CELERY_BEAT_SCHEDULE` starts empty)

## Local vs production

| Concern | Local | Production |
|---------|-------|------------|
| Settings | `config.django.base` / local overlays | production settings + env |
| Static | WhiteNoise / runserver | collectstatic in entrypoint |
| Process | `make run` | gunicorn via entrypoint |

## Related

- [Getting Started](../getting-started.md)
- [Secrets Management](secrets-management.md)
