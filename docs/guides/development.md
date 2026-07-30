# Development Guide

This guide covers development setup, workflow, and best practices for the EHR Practitioner Service.

## Development Setup

### Prerequisites

- Python 3.12+
- PostgreSQL
- Docker & Docker Compose (optional)
- Git

### Initial Setup

1. Clone the repository
2. Create virtual environment
3. Install dependencies: `make update`
4. Configure environment variables
5. Run migrations: `python manage.py migrate`
6. Start development server: `make run`

## Development Workflow

### Code Style

- Follow PEP 8 guidelines
- Use Ruff for linting and formatting
- Run `ruff check .` and `ruff format .` before committing

### Testing

- Write tests for all new features
- Run tests: `pytest`
- Maintain 80%+ test coverage
- Use pytest fixtures for test data

### Model Creation

- Follow the [Django Modeling Standard](../standards/modeling.md)
- Include proper docstrings
- Add help_text to all fields
- Use proper related_name patterns

### Git Workflow

- Create feature branches
- Write descriptive commit messages
- Run tests before pushing
- Create pull requests for review

## Common Tasks

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=core --cov-report=html

# Specific test file
pytest core/practitioners/tests/test_models.py
```

### Seeding Data

```bash
make seed-practitioners COUNT=10
```

## Debugging

- Use Django Debug Toolbar in development
- Check logs in `logs/` directory
- Use Django shell: `python manage.py shell`

## Related Documentation

- [Testing Guide](testing.md)
- [Modeling Standard](../standards/modeling.md)

