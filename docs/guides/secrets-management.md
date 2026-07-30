# Secrets Management

How this template loads sensitive bootstrap credentials (superusers).

## Overview

Superuser credentials live in a **YAML file** on disk. The path is set with:

```bash
DJANGO_SECRETS_FILE_PATH=.secrets.yml
```

`.secrets.yml` is gitignored. Do not commit real passwords.

## Quick start

```bash
# .env
DJANGO_SECRETS_FILE_PATH=.secrets.yml

make seed-superuser
make seed-superuser UPDATE=1
```

## YAML format

```yaml
superusers:
  - email: admin@example.com
    phone_number: 251900000000
    password: "use-a-strong-unique-password"
    # optional:
    username: admin          # default: email local-part
    id: afe45de5-a6fe-46fb-b0da-c27a26879012
    first_name: Admin        # ignored by User model if fields removed; safe to omit
    last_name: User
```

Required fields per entry: `email`, `password`, `phone_number`.

## Security

- Keep the file out of git and shared channels
- Use unique strong passwords (HIBP-backed validators may reject breached passwords)
- Prefer a dedicated JWT signing key in production (`DJANGO_JWT_SIGNING_KEY`)
- Rotate credentials when compromised

## Related

- [Seeding](seeding.md)
- Command docs: `core/common/management/commands/docs/load_superusers.md`
- Loader: `core/common/management/commands/secrets_loader.py`
