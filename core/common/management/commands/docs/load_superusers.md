# Load Superusers

Django management command to load superusers from a YAML secrets file.

## Overview

This command reads superuser credentials from a YAML file (path specified via `SECRETS_FILE_PATH` environment variable) and creates or updates them in the database.

## Usage

### Basic Usage

```bash
# Load superusers (skip if already exists)
python manage.py load_superusers

# Using Makefile
make seed-superuser
```

### Update Existing Users

```bash
# Update existing superusers
python manage.py load_superusers --update

# Using Makefile
make seed-superuser UPDATE=1
```

### Dry Run

```bash
# Preview changes without applying
python manage.py load_superusers --dry-run
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--update` | Update existing superusers | `False` |
| `--force` | Same as `--update` | `False` |
| `--dry-run` | Preview changes without applying | `False` |

## YAML File Format

The secrets file should be in YAML format with a `superusers` list:

```yaml
superusers:
  - email: admin@example.com
    phone_number: "+251931470920"
    password: StrongPassword123!
    first_name: Admin
    last_name: User
```

### Required Fields

- `email`: User email address (must be unique)
- `phone_number`: Phone number (string with + or integer)
- `password`: User password
- `first_name`: First name
- `last_name`: Last name

## Environment Configuration

Set the secrets file path in your `.env` file:

```bash
SECRETS_FILE_PATH="/path/to/.secrets.yml"
```

## Behavior

### Default (No `--update`)

- Creates new superusers if they don't exist
- Skips existing users (no changes)

### With `--update`

- Creates new superusers if they don't exist
- Updates existing users (password, name, phone_number)

### With `--dry-run`

- Shows what would be created/updated
- Makes no actual changes

## Examples

### Example 1: Create Superusers

```bash
$ python manage.py load_superusers
Found 4 superuser(s) in secrets file
  [1] Created: yeabsera.dev@gmail.com
  [2] Created: yoseph.dev@gmail.com
  [3] Created: abel.dev@gmail.com
  [4] Created: tadesse.dev@gmail.com

SUMMARY:
  Created: 4
```

### Example 2: Update Existing Users

```bash
$ python manage.py load_superusers --update
Found 4 superuser(s) in secrets file
  [1] Updated: yeabsera.dev@gmail.com
  [2] Updated: yoseph.dev@gmail.com
  [3] Updated: abel.dev@gmail.com
  [4] Updated: tadesse.dev@gmail.com

SUMMARY:
  Updated: 4
```

### Example 3: Dry Run

```bash
$ python manage.py load_superusers --dry-run
DRY RUN MODE - No changes will be made
Found 4 superuser(s) in secrets file
  [1] Would create: yeabsera.dev@gmail.com
  [2] Would create: yoseph.dev@gmail.com
  [3] Would create: abel.dev@gmail.com
  [4] Would create: tadesse.dev@gmail.com

DRY RUN SUMMARY:
  Created: 4
```

## Error Handling

The command validates:

- Secrets file exists and is readable
- YAML syntax is valid
- Required fields are present
- Email format is valid
- Phone number format is valid
- Password is not empty

## Security

- Never commit `.secrets.yml` to Git
- Use `chmod 600` to restrict file permissions
- Use different files for different environments
- Rotate passwords regularly

## Related

- [Secrets Management Guide](../../../../docs/SECRETS_MANAGEMENT_GUIDE.md) - Comprehensive guide
- `core/common/utils/secrets_loader.py` - Utility functions

