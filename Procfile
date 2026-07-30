web: uv run python manage.py runserver 6000
celery: uv run celery -A config.settings.celery worker --loglevel=info --pool=solo
celery-beat: uv run celery -A config.settings.celery beat --loglevel=info
