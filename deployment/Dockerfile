FROM python:3.12.4-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:/root/.cargo/bin:$PATH

# Install build dependencies (libffi-dev for cffi-backed wheels e.g. WeasyPrint deps)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    binutils \
    git \
    curl \
    libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /usr/src/app

# Copy dependency files (these change less frequently)
COPY pyproject.toml uv.lock* ./
COPY scripts/install.sh ./scripts/
COPY .env ./.env

# Install dependencies
RUN chmod +x ./scripts/install.sh && ./scripts/install.sh

# Verify virtual environment was created and Django is installed
RUN test -d .venv && .venv/bin/python -c "import django; print(f'Django {django.__version__} installed')" || (echo "ERROR: Virtual environment or Django not found!" && exit 1)

# Runtime stage
FROM python:3.12.4-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/usr/src/app/.venv/bin:$PATH

# WeasyPrint PDF rendering (document generation Celery tasks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libharfbuzz-subset0 \
    shared-mime-info \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user
RUN groupadd -g 1000 app && useradd -m -u 1000 -g app appuser

WORKDIR /usr/src/app

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:app /usr/src/app/.venv /usr/src/app/.venv

# Fix Python symlinks to point to the correct Python in runtime stage
# The venv may have symlinks pointing to /usr/bin/python3 which doesn't exist in python:3.12.4-slim
RUN rm -f /usr/src/app/.venv/bin/python /usr/src/app/.venv/bin/python3 /usr/src/app/.venv/bin/python3.12 2>/dev/null || true && \
    ln -s /usr/local/bin/python3 /usr/src/app/.venv/bin/python && \
    ln -s python /usr/src/app/.venv/bin/python3 && \
    ln -s python /usr/src/app/.venv/bin/python3.12

# Verify venv exists before copying app source
RUN test -d /usr/src/app/.venv && echo "Virtual environment copied successfully" || (echo "ERROR: Virtual environment not found!" && exit 1)

# Copy application source (already includes submodules)
COPY --chown=appuser:app . .

# Copy and set up entrypoints
COPY --chown=appuser:app deployment/entrypoint.sh /usr/src/app/entrypoint.sh
COPY --chown=appuser:app deployment/worker-entrypoint.sh /usr/src/app/deployment/worker-entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh /usr/src/app/deployment/worker-entrypoint.sh

# Create logs and staticfiles directories (chown only these, not entire tree - COPY already set ownership)
RUN mkdir -p /usr/src/app/logs /usr/src/app/staticfiles && \
    chown appuser:app /usr/src/app/logs /usr/src/app/staticfiles

USER appuser

CMD ["./entrypoint.sh"]