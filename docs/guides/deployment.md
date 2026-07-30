# Deployment Guide

This guide covers deployment procedures for the EHR Practitioner Service.

## Deployment Environments

### Development

Development deployment using Docker Compose.

See `docker/development/README.md` for details.

### Production

Production deployment with proper security and scaling.

See `docker/production/README.md` for details.

## Deployment Steps

### 1. Pre-Deployment

- Run all tests: `pytest`
- Check code quality: `ruff check .`
- Review migrations
- Update environment variables

### 2. Build

```bash
docker build -t ehr-practitioner-service:latest .
```

### 3. Deploy

```bash
docker-compose up -d
```

### 4. Post-Deployment

- Verify health endpoints
- Check logs
- Monitor metrics
- Run smoke tests

## Environment Variables

Required environment variables:
- Database configuration
- Secret keys
- Service URLs
- Authentication settings

## Monitoring

- Health checks
- Log aggregation
- Error tracking (Sentry)
- Performance monitoring

## Related Documentation

- [Development Guide](development.md)
- [Configuration Reference](../reference/configuration.md)

