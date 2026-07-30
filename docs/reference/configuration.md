# Configuration Reference

This document provides a reference for configuration options in the EHR Practitioner Service.

## Environment Variables

### Database

- `DATABASE_URL` - Database connection string
- `DATABASE_NAME` - Database name
- `DATABASE_USER` - Database user
- `DATABASE_PASSWORD` - Database password
- `DATABASE_HOST` - Database host
- `DATABASE_PORT` - Database port

### Application

- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `ALLOWED_HOSTS` - Allowed hosts (comma-separated)

### Authentication

- `KEYCLOAK_URL` - Keycloak server URL
- `KEYCLOAK_REALM` - Keycloak realm
- `KEYCLOAK_CLIENT_ID` - Keycloak client ID

### Secrets

- `SECRETS_FILE_PATH` - Path to secrets YAML file

## Django Settings

Settings are organized in `config/settings/`:
- `base.py` - Base settings
- `django/production.py` - Production settings
- `django/test.py` - Test settings

## Related Documentation

- [Development Guide](../guides/development.md)
- [Deployment Guide](../guides/deployment.md)

