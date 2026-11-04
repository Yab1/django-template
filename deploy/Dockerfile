FROM python:3.12.4-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:/root/.cargo/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    binutils \
    git \
    curl \
    libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /usr/src/app

COPY pyproject.toml uv.lock* ./
COPY scripts/install.sh ./scripts/

RUN chmod +x ./scripts/install.sh && ./scripts/install.sh

RUN test -d .venv && .venv/bin/python -c "import django; print(f'Django {django.__version__} installed')" || (echo "ERROR: Virtual environment or Django not found!" && exit 1)

FROM python:3.12.4-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/usr/src/app/.venv/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    binutils \
    gdal-bin \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libharfbuzz-subset0 \
    shared-mime-info \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN groupadd -g 1000 app && useradd -m -u 1000 -g app appuser

WORKDIR /usr/src/app

COPY --from=builder --chown=appuser:app /usr/src/app/.venv /usr/src/app/.venv

RUN rm -f /usr/src/app/.venv/bin/python /usr/src/app/.venv/bin/python3 /usr/src/app/.venv/bin/python3.12 2>/dev/null || true && \
    ln -s /usr/local/bin/python3 /usr/src/app/.venv/bin/python && \
    ln -s python /usr/src/app/.venv/bin/python3 && \
    ln -s python /usr/src/app/.venv/bin/python3.12

RUN test -d /usr/src/app/.venv && echo "Virtual environment copied successfully" || (echo "ERROR: Virtual environment not found!" && exit 1)

COPY --chown=appuser:app . .

COPY --chown=appuser:app deploy/entrypoint.sh /usr/src/app/entrypoint.sh
COPY --chown=appuser:app deploy/worker-entrypoint.sh /usr/src/app/deploy/worker-entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh /usr/src/app/deploy/worker-entrypoint.sh

RUN mkdir -p /usr/src/app/logs /usr/src/app/staticfiles && \
    chown appuser:app /usr/src/app/logs /usr/src/app/staticfiles

USER appuser

EXPOSE 8000

CMD ["./entrypoint.sh"]
