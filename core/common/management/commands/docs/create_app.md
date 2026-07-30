# Create App

Django management command to create a new Django app under `core/` with standard scaffolding.

## Overview

This command creates a new Django app in the `core/` directory with:

- Standard Django app structure
- REST API scaffolding: `services.py`, `selectors.py`, `apis.py`, `urls.py`
- Proper app configuration
- Migrations directory

## Usage

### Basic Usage

```bash
# Create a new app
python manage.py create_app <app_name>

# Example: Create a reports app
python manage.py create_app reports
```

### With Auto-Registration

```bash
# Create app and automatically register it in settings
python manage.py create_app reports --register
```

### Using Makefile

```bash
# Create app
make create-app APP=reports

# Create and register app
make create-app APP=reports REGISTER=1
```

## Options

| Option | Description | Example |
|--------|-------------|---------|
| `app_name` | Name of the app to create (required) | `reports` |
| `--register` | Automatically register app in `LOCAL_APPS` | `--register` |

## What It Creates

When you run `python manage.py create_app reports`, it creates:

```
core/
└── reports/
    ├── __init__.py
    ├── admin.py
    ├── apps.py          # Configured with name = "core.reports"
    ├── models.py
    ├── migrations/
    │   └── __init__.py
    ├── services.py      # Business logic / use cases
    ├── selectors.py     # Read-only queries (list, get)
    ├── apis.py          # REST API views (DRF or plain Django views)
    └── urls.py          # URL routing for this app
```

## App Configuration

The command automatically configures `apps.py` with the correct app name:

```python
# core/reports/apps.py
class ReportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.reports"  # Automatically set
```

## Auto-Registration

When using `--register`, the command attempts to add the app to `config/django/base.py`:

```python
LOCAL_APPS = [
    "core.reports.apps.ReportsConfig",  # Automatically added
    # ... other apps
]
```

**Note:** The command only adds the app if:
- The `LOCAL_APPS` list exists in `config/django/base.py`
- The app is not already registered (checks both `LOCAL_APPS` and `INSTALLED_APPS`)
- The file is writable

If the app is already registered, the command will display a warning message and skip registration.

## Examples

### Create a basic app

```bash
python manage.py create_app reports
```

This creates `core/reports/` with all necessary files.

### Create and register app

```bash
python manage.py create_app reports --register
```

This creates the app and automatically adds it to `LOCAL_APPS`.

### Create app with specific name

```bash
# Valid: lowercase with underscores
python manage.py create_app user_profiles

# Valid: single word
python manage.py create_app analytics

# Invalid: will raise error
python manage.py create_app "user-profiles"  # Contains hyphen
python manage.py create_app "UserProfiles"   # Starts with capital
```

## Requirements

- App name must be a valid Python identifier (letters, numbers, underscores, cannot start with number)
- App directory must not already exist
- Django project must be properly configured

## Error Handling

### App Already Exists

```bash
$ python manage.py create_app reports
CommandError: App directory already exists: /path/to/core/reports
```

**Solution:** Use a different app name or remove the existing directory.

### Invalid App Name

```bash
$ python manage.py create_app "user-profiles"
CommandError: Invalid app name: 'user-profiles'
```

**Solution:** Use a valid Python identifier (no hyphens, no spaces, etc.).

### Registration Failed

If `--register` is used but registration fails:

- The app is still created successfully
- You'll need to manually add it to `LOCAL_APPS`
- Check that `config/django/base.py` exists and is writable

## Next Steps

After creating an app:

1. **Add models** in `models.py` - Follow the [Django FHIR Modeling Standard](../../../../docs/standards/modeling.md) if applicable
   - **Important**: For nested component models used in `ManyToManyField` relationships, use shorter `db_table` names to avoid intermediary table conflicts
2. **Create migrations**: `python manage.py makemigrations <app_name>`
3. **Apply migrations**: `python manage.py migrate`
4. **Implement REST API**: add selectors in `selectors.py`, business logic in `services.py`, views in `apis.py`, and wire routes in `urls.py` (then include in project URLs)
5. **Register in admin** (optional) in `admin.py`

## Related Commands

- `python manage.py makemigrations` - Create database migrations
- `python manage.py migrate` - Apply migrations
- `python manage.py createsuperuser` - Create admin user
