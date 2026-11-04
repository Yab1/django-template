# Deploy

Blue-green API + Celery worker/beat, Jenkins-ready. Infra (PostGIS/Redis/RabbitMQ/Mailpit/MinIO) stays in [`../infra`](../infra).

Create **`deploy/.env`** yourself (Compose `env_file` — no `export`). Same keys as root `.env.example`; inside Docker use hostnames `postgres`, `redis`, `rabbitmq`, `minio` not `localhost`. Set `RABBITMQ_HOST=rabbitmq`.

## Layout

| Path | Role |
|------|------|
| `Dockerfile` | Multi-stage uv/Python image. curl in runtime for `/health/`. No `.env` copied into the image. |
| `docker-compose.yml` | `api_blue`, `api_green`, `worker`, `beat`, `proxy`, migrate/seed tools |
| `nginx/app-active.conf.template` | Proxy upstream placeholder |
| `scripts/deploy.sh` | Migrate one-shot → new slot → `/health/` → switch → stop old → workers |
| `scripts/seed.sh` | `load_superusers` |
| `Jenkinsfile` | Checkout → env → deploy → seed |

API and worker **never** migrate. Seed **never** runs on API boot.

## Names

| Thing | Name |
|-------|------|
| Compose project | `django_template` |
| Image | `django_template:latest` |
| API slots | `django_template_api_blue`, `django_template_api_green` |
| Celery | `django_template_worker`, `django_template_beat` |
| Proxy | `django_template_api_proxy` |
| Networks | `django_template` (infra) |

## Host flow

```bash
make infra-up
# create deploy/.env
make deploy
make deploy-seed
```

Proxy publishes `APP_PORT` (default 8000) → active slot.

## Jenkins

Job: `deploy/Jenkinsfile`. Run `infra/Jenkinsfile` first. Lint and test stay on GitHub Actions (`.github/workflows/ci.yml`); require that workflow before merging so `main` is already green. Jenkins copies `JENKINS_ENV_FILE` → `deploy/.env`, then `deploy.sh` then `seed.sh`.
