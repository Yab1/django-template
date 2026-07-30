# Seeding Guide

This template ships **one** seed path: superusers from a YAML secrets file.

## Quick start

```bash
make seed-superuser
make seed-superuser UPDATE=1   # update existing accounts
```

Equivalent:

```bash
python manage.py load_superusers
python manage.py load_superusers --update
python manage.py load_superusers --dry-run
```

Requires `DJANGO_SECRETS_FILE_PATH` (see [Secrets Management](secrets-management.md)).

## What it creates

- Staff / superuser / admin flags set
- Username from YAML `username` or email local-part
- Optional fixed UUID via `id` in YAML

Password must satisfy Django validators (length, common passwords, HIBP where configured).

## Not included

There are no practitioner / patient / FHIR / terminology seed targets in this template. Domain seeds belong in product apps you add later.

## Command docs

Longer reference: [`core/common/management/commands/docs/load_superusers.md`](../../core/common/management/commands/docs/load_superusers.md).
