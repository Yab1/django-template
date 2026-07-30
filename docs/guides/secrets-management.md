# Secrets Management Guide

This guide covers secrets management in the EHR Practitioner Service.

## Overview

The service includes a secure secrets management system for handling sensitive configuration data like superuser credentials.

## Quick Start

```bash
# Load superusers from YAML secrets file
make seed-superuser

# Update existing superusers
make seed-superuser UPDATE=1
```

## Secrets File Format

Secrets are stored in YAML format:

```yaml
superusers:
  - email: admin@example.com
    password: secure_password
    is_superuser: true
    is_staff: true
```

## Configuration

The secrets file path is configured via environment variable:

```bash
export SECRETS_FILE_PATH=/path/to/secrets.yaml
```

## Security

- Secrets file never committed to Git
- Use environment variables for file path
- Store secrets in secure location
- Rotate secrets regularly

## Features

- **YAML-based**: Store secrets in YAML format
- **Environment-driven**: File path configured via env var
- **Secure**: Secrets file never committed
- **Flexible**: Works with Docker, local, and production

## Related Documentation

- [Development Guide](development.md)
- [Deployment Guide](deployment.md)

