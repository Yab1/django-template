# Generate gRPC Token

Django management command to generate JWT bearer tokens for gRPC service-to-service authentication.

## Overview

This command generates JWT tokens that can be used for authenticating gRPC requests between services. The tokens are signed with `SERVICE_TOKEN_SECRET` and include service identity, roles, and expiration information.

## Usage

### Basic Usage

```bash
# Generate token with default settings (from .env)
python manage.py generate_grpc_token

# Or using Makefile
make generate-grpc-token
```

### Advanced Usage

```bash
# Specify service name
python manage.py generate_grpc_token --service-name ehr_patient

# Specify roles (comma-separated, no spaces)
python manage.py generate_grpc_token --roles admin,reader,writer

# Set token expiration (in seconds)
python manage.py generate_grpc_token --ttl 7200  # 2 hours

# Combine options
python manage.py generate_grpc_token \
    --service-name ehr_patient \
    --roles admin,reader,writer \
    --ttl 3600
```

## Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--service-name` | Service identifier | `settings.SERVICE_NAME` | `ehr_patient` |
| `--roles` | Comma-separated roles | `settings.SERVICE_ROLES` | `admin,reader,writer` |
| `--ttl` | Token expiration in seconds | `3600` (1 hour) | `7200` |
| `--format` | Output format | `token` | `token`, `header`, `curl` |

## Output Formats

### `token` (default)

Just the raw JWT token:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### `header`

Full authorization header:

```
Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### `curl`

Ready-to-use curl command:

```bash
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  http://localhost:50054
```

## Environment Variables

The command uses these environment variables (from `.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVICE_NAME` | Service identifier | `ehr_patient` |
| `SERVICE_ROLES` | Comma-separated roles | (empty) |
| `SERVICE_TOKEN_SECRET` | Secret for signing tokens | `SECRET_KEY` |
| `SERVICE_TOKEN_AUDIENCE` | Token audience | `tilla-services` |
| `SERVICE_TOKEN_ISSUER` | Token issuer | `tilla-id` |

## Token Structure

The generated JWT token contains:

```json
{
  "iss": "tilla-id",              // Issuer
  "aud": "tilla-services",        // Audience
  "sub": "ehr_patient",           // Subject (service name)
  "service": "ehr_patient",        // Service identifier
  "iat": 1234567890,              // Issued at
  "exp": 1234571490,               // Expires at
  "roles": ["admin", "reader", "writer"]  // Service roles
}
```

## Examples

### Generate token for testing in Postman

```bash
python manage.py generate_grpc_token --roles admin,reader,writer
```

Then in Postman:

1. Go to your gRPC request
2. Click on **Metadata** tab
3. Add header:
   - Key: `authorization`
   - Value: `Bearer <your-token>`

### Generate token with custom expiration

```bash
# Token valid for 30 minutes
python manage.py generate_grpc_token --ttl 1800

# Token valid for 24 hours
python manage.py generate_grpc_token --ttl 86400
```

### Generate token for different service

```bash
python manage.py generate_grpc_token \
    --service-name ehr_tenant \
    --roles admin,reader
```

## Setting Roles

### Method 1: Command Line (Recommended for Testing)

```bash
python manage.py generate_grpc_token --roles admin,reader,writer
```

**Note:** Use comma-separated values without spaces (e.g., `admin,reader,writer`, not `admin, reader, writer`).

### Method 2: Environment Variable (Default)

Set in your `.env` file:

```bash
SERVICE_ROLES=admin,reader,writer
```

Then when you run:

```bash
python manage.py generate_grpc_token
```

It will automatically use the roles from `SERVICE_ROLES`.

## Token Validation

The generated tokens are validated by the `ServiceAuthInterceptor` in `core/grpc/interceptors/auth.py`. The interceptor checks:

- ✅ Token signature (matches `SERVICE_TOKEN_SECRET`)
- ✅ Token expiration (`exp` claim)
- ✅ Token audience (`aud` claim)
- ✅ Token issuer (`iss` claim)
- ✅ Service identity (`sub` or `service` claim)
- ✅ Required roles (if specified)

## Troubleshooting

### Token not accepted by server

1. **Check secret matches**: Ensure `SERVICE_TOKEN_SECRET` in `.env` matches the server's secret
2. **Check audience/issuer**: Ensure `SERVICE_TOKEN_AUDIENCE` and `SERVICE_TOKEN_ISSUER` match server expectations
3. **Check expiration**: Token may have expired. Generate a new one with longer TTL:

   ```bash
   python manage.py generate_grpc_token --ttl 7200  # 2 hours
   ```

### Token missing roles

If roles are not included in the token:

1. Set `SERVICE_ROLES` in `.env`, or
2. Use `--roles` flag when generating:

   ```bash
   python manage.py generate_grpc_token --roles admin,reader
   ```

## Related Documentation

- [gRPC Authentication Guide](../../../../core/grpc/AUTHENTICATION.md)
- [Service Auth Interceptor](../../../../core/grpc/interceptors/auth.py)

