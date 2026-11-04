# Deployment Guide

Production-oriented deploy notes for this template.

## Layout

```text
infra/                   # Postgres, Redis, RabbitMQ, Mailpit, MinIO (+ optional ClamAV)
deploy/
  docker-compose.yml     # blue/green API, worker, beat, nginx proxy, migrate/seed
  Dockerfile
  scripts/deploy.sh      # blue-green Docker deploy
  entrypoint.sh          # collectstatic, then gunicorn (migrate is one-shot)
  worker-entrypoint.sh
  gunicorn.config.py
  nginx/                 # active upstream config for proxy
  Jenkinsfile            # app CI/CD pipeline (when used)
```

## Infra first

```bash
cp infra/.env.example infra/.env   # edit ports/passwords if needed
make infra-up                      # or: make -C infra up
```

Creates external Docker network `django_template` that the app compose joins.

## Health check

Deploy waits on:

```text
GET /health/
```

Not under `/api/v1/`. Returns 200 when probes are ok / `not_configured`, 503 when unhealthy.

See [REST API Overview](../api/rest/overview.md) for probe details.

## Blue-green (Docker)

[`deploy/scripts/deploy.sh`](../../deploy/scripts/deploy.sh):

1. Ensure infra network exists
2. Run migrate one-shot
3. Bring up the inactive API slot
4. Wait for entrypoint marker + HTTP `/health/`
5. Switch nginx upstream
6. Stop the old slot
7. Recreate worker + beat

Proxy / slot names use the `django_template_*` prefix in this template.

```bash
make deploy          # blue-green roll
make deploy-seed     # load_superusers via tools profile
make status          # orchestrate status
```

## Runtime expectations

- Set production env (see [Configuration](../reference/configuration.md) and `.env.example`)
- Keep app `RABBITMQ_*` in sync with `infra/.env`
- `DJANGO_DEBUG=False`, strong `DJANGO_SECRET_KEY` / JWT signing key
- Secrets file available to the container if you run `load_superusers` in ops (usually seed once, not every deploy)
- Celery worker + beat: notifications dispatch is in `CELERY_BEAT_SCHEDULE`

## Local vs production

| Concern | Local | Production |
|---------|-------|------------|
| Settings | `config.django.base` / local overlays | production settings + env |
| Static | WhiteNoise / runserver | collectstatic in entrypoint |
| Process | `make run` / `make dev` | gunicorn via entrypoint |
| Deps | `make infra-up` or host services | same infra compose on host/agent |

## Related

- [Getting Started](../getting-started.md)
- [Secrets Management](secrets-management.md)
- [`deploy/README.md`](../../deploy/README.md)
- [`infra/README.md`](../../infra/README.md)
