# Testing Guide

This guide covers testing practices and guidelines for the EHR Practitioner Service.

## Testing Framework

The service uses:
- **pytest** - Testing framework
- **pytest-django** - Django integration
- **pytest-cov** - Coverage reporting
- **factory-boy** - Test data generation
- **faker** - Realistic test data

## Test Organization

Tests are organized by domain and type:

```
core/
└── practitioners/
    └── tests/
        ├── models/
        │   └── test_practitioner.py
        ├── services/
        │   └── test_practitioner_service.py
        └── mutations/
            └── test_create_practitioner.py
```

## Writing Tests

### Model Tests

```python
import pytest
from core.practitioners.models import Practitioner

@pytest.mark.django_db
def test_practitioner_creation():
    practitioner = Practitioner.objects.create(
        name="Dr. John Doe",
        active=True
    )
    assert practitioner.id is not None
    assert practitioner.active is True
```

### Service Tests

```python
from core.practitioners.services import PractitionerService

@pytest.mark.django_db
def test_create_practitioner():
    service = PractitionerService()
    practitioner = service.create(name="Dr. Jane Doe")
    assert practitioner.name == "Dr. Jane Doe"
```

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=core --cov-report=html

# Specific test
pytest core/practitioners/tests/test_models.py

# Parallel execution
pytest -n auto
```

## Test Coverage

- Target: 80% minimum coverage
- Run: `pytest --cov=core --cov-report=html`
- View: Open `htmlcov/index.html` in browser

## Best Practices

1. Write tests before code (TDD)
2. Test edge cases and error conditions
3. Use descriptive test names
4. Keep tests isolated and independent
5. Use fixtures for common setup
6. Mock external dependencies

## Related Documentation

- [Development Guide](development.md)
- [Seeding Guide](seeding.md)

