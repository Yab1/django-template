COMPOSE = docker compose \
	-f compose.yml \
	-f compose.postgres.yml \
	-f compose.redis.yml \
	-f compose.rabbitmq.yml \
	-f compose.mailpit.yml \
	-f compose.minio.yml \
	-f compose.clamav.yml \
	--env-file .env

.PHONY: env up up-scanning down stop logs ps restart reset help

help:
	@echo "infra targets:"
	@echo "  make up            start postgres redis rabbitmq mailpit minio"
	@echo "  make up-scanning   also start clamav (virus scan on upload)"
	@echo "  make down          stop and remove containers"
	@echo "  make stop          stop containers"
	@echo "  make logs s=X      follow logs (e.g. s=redis)"
	@echo "  make ps            list containers"
	@echo "  make restart       restart Django Template infra services"
	@echo "  make reset         down + delete volumes (destructive)"

env:
	@test -f .env || cp .env.example .env
	@echo ".env ready"

up: env
	@$(COMPOSE) up -d
	@echo "postgres         → localhost:$${POSTGRES_PORT:-5432}"
	@echo "redis            → localhost:$${REDIS_PORT:-6379}"
	@echo "rabbitmq AMQP    → localhost:$${RABBITMQ_PORT:-5672}"
	@echo "rabbitmq UI      → http://localhost:$${RABBITMQ_MANAGEMENT_PORT:-15672}"
	@echo "mailpit UI       → http://localhost:$${MAILPIT_UI_PORT:-8025}"
	@echo "mailpit SMTP     → localhost:$${MAILPIT_SMTP_PORT:-1025}"
	@echo "minio API        → localhost:$${MINIO_API_PORT:-9000}"
	@echo "minio console    → http://localhost:$${MINIO_CONSOLE_PORT:-9001}"
	@echo "(clamav: make up-scanning)"

up-scanning: env
	@$(COMPOSE) --profile scanning up -d
	@echo "postgres         → localhost:$${POSTGRES_PORT:-5432}"
	@echo "redis            → localhost:$${REDIS_PORT:-6379}"
	@echo "rabbitmq AMQP    → localhost:$${RABBITMQ_PORT:-5672}"
	@echo "rabbitmq UI      → http://localhost:$${RABBITMQ_MANAGEMENT_PORT:-15672}"
	@echo "mailpit UI       → http://localhost:$${MAILPIT_UI_PORT:-8025}"
	@echo "mailpit SMTP     → localhost:$${MAILPIT_SMTP_PORT:-1025}"
	@echo "minio API        → localhost:$${MINIO_API_PORT:-9000}"
	@echo "minio console    → http://localhost:$${MINIO_CONSOLE_PORT:-9001}"
	@echo "clamav           → localhost:$${CLAMAV_PORT:-3310} (first start downloads signatures)"

down:
	@$(COMPOSE) --profile scanning down

stop:
	@$(COMPOSE) --profile scanning stop

logs:
	@$(COMPOSE) logs -f $(s)

ps:
	@$(COMPOSE) --profile scanning ps

restart:
	@$(COMPOSE) restart $(or $(s),postgres redis rabbitmq mailpit minio)

# Wipe named volumes. Destructive.
reset:
	@$(COMPOSE) --profile scanning down -v
