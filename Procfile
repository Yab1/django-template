web: uv run python manage.py runserver 7000
celery: uv run celery -A config.settings.celery worker --loglevel=info --pool=solo
celery-beat: uv run celery -A config.settings.celery beat --loglevel=info
temporal: uv run python -m core.workflows.temporal.worker
