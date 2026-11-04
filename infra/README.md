# Infra

Third-party services for Django Template. App code stays under `core/` / `config/`; this folder owns shared dependencies.

## Layout

| File | Role |
|------|------|
| `compose.yml` | Shared project name + `django_template` network |
| `compose.postgres.yml` | PostGIS (Postgres 18 + PostGIS 3.6) |
| `compose.redis.yml` | Redis (cache + Channels; not Celery) |
| `compose.rabbitmq.yml` | RabbitMQ + management UI (Celery broker) |
| `compose.mailpit.yml` | Mailpit (SMTP + UI) |
| `compose.minio.yml` | MinIO (create buckets in console) |
| `compose.clamav.yml` | ClamAV (`profile: scanning`; `make up-scanning`) |
| `postgres/init/10-postgis.sql` | `CREATE EXTENSION postgis` on empty volume |
| `.env.example` | Defaults (copy to `.env`) |
| `Jenkinsfile` | Jenkins: Checkout → PRECHECK → env → deploy → POST |
| `scripts/config.sh` | Jenkins env path (`JENKINS_ENV_FILE`) |
| `scripts/deploy.sh` | `make up` + health wait |

Default `make up` = postgres + redis + rabbitmq + mailpit + minio.
ClamAV stays off until `make up-scanning` (upload virus scan).

## Usage

```bash
cd infra
cp .env.example .env   # once
make up
make logs s=rabbitmq
make down
make reset             # down + delete volumes
```

From the repo root: `make infra-up` / `make infra-down`.

| Service | Host | Started by |
|---------|------|------------|
| PostGIS | `localhost:${POSTGRES_PORT}` | `make up` |
| Redis | `localhost:${REDIS_PORT}` | `make up` |
| RabbitMQ AMQP | `localhost:${RABBITMQ_PORT}` | `make up` |
| RabbitMQ UI | `http://localhost:${RABBITMQ_MANAGEMENT_PORT}` | `make up` |
| Mailpit UI / SMTP | `${MAILPIT_UI_PORT}` / `${MAILPIT_SMTP_PORT}` | `make up` |
| MinIO | `${MINIO_API_PORT}` / console `${MINIO_CONSOLE_PORT}` | `make up` |
| ClamAV | `${CLAMAV_PORT}` | `make up-scanning` |

If 5432 / 5672 / 6379 / 9000 / 15672 are already taken on this host, remap host ports in `infra/.env`.

App `.env` tips:

- `DJANGO_DB_*` matches `POSTGRES_*`
- `RABBITMQ_USER` / `PASSWORD` / `VHOST` match infra. Host is `localhost` on the machine, `rabbitmq` inside Docker.
- Leave `CELERY_BROKER_URL` empty unless you need an override; settings assemble it from `RABBITMQ_*`.
- `DJANGO_CACHE_REDIS_URL` uses Redis DB `/1`; `DJANGO_CHANNEL_REDIS_URL` uses `/2`
- SMTP: `DJANGO_EMAIL_HOST=localhost`, `DJANGO_EMAIL_PORT=1025`
- MinIO: create buckets in console once (`MINIO_BUCKET`, plus a static bucket if used)

## PostGIS upgrade (existing plain Postgres 18 volume)

Init SQL runs **only** on an empty data directory. A volume created under `postgres:18` keeps working under `postgis/postgis:18-3.6` (same major), but the extension is missing until you create it.

1. Backup: `docker exec django_template_postgres pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB" > django_template.dump`
2. `make infra-down` (keep the volume; do **not** `make reset`)
3. Pull / start the PostGIS image (`make infra-up`)
4. Enable the extension as the compose superuser (`POSTGRES_USER`):

```bash
docker exec django_template_postgres \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c 'CREATE EXTENSION IF NOT EXISTS postgis;'
```

5. From the repo root: `uv run python manage.py migrate` (applies `common.0001_postgis`, which is idempotent)

Wipe + recreate (`make reset` then `make up`) if you can throw the volume away: init SQL + migrate both enable PostGIS.

`POSTGRES_USER` in this compose file is a superuser, so `CREATE EXTENSION` works. A least-privilege app role in production needs a DBA to run that statement once.

## Jenkins

Job: `infra/Jenkinsfile`. Agent needs Docker + Compose.

Stages: Checkout → **Prepare Environment** → PRECHECK → Deploy → POST.

1. Put host env on the agent at path from `scripts/config.sh` (default `/var/lib/jenkins/api/django-template/django_template_infra.env`) — same keys as `.env.example`.
2. Pipeline copies that file → `infra/.env` **before** compose validate (services use `env_file: .env`).

Run this job **before** `deploy/Jenkinsfile` so PostGIS / Redis / RabbitMQ exist for the API.
