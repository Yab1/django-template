# REST API Overview

Public HTTP surface for Django Template.

## Base URLs

| Prefix | Use |
|--------|-----|
| `/api/v1/` | Versioned REST APIs |
| `/health/` | Infra health (no `/api/v1`) |
| `/schema/`, `/docs/`, `/redoc/` | OpenAPI / Swagger / ReDoc (admin session) |

Success responses are wrapped by `EnvelopeJSONRenderer`:

```json
{
  "status": "success",
  "result": {},
  "meta": { "version": "v1" },
  "message": "Request processed successfully"
}
```

Views return the **inner** `result` payload; the renderer adds the envelope for 2xx.

## Authentication (`core.authentication`)

Mounted at `/api/v1/authentication/`.

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| POST | `/authentication/token/` | none | username + password → access + refresh |
| POST | `/authentication/token/refresh/` | none | refresh → new access (rotation) |
| POST | `/authentication/token/verify/` | none | verify token |
| POST | `/authentication/token/blacklist/` | none | logout (blacklist refresh) |
| GET | `/authentication/me/` | Bearer | current user; allowed if `must_change_password` |
| POST | `/authentication/me/password/` | Bearer | change own password |
| POST | `/authentication/password-reset/confirm/` | none | uid + token + new_password |

Use header `Authorization: Bearer <access>` (Postman collections use the `auth` bearer property).

## Users (`core.users`)

Mounted under `/api/v1/users/` (via users app URLs).

| Method | Path | Notes |
|--------|------|-------|
| GET | `/users/` | paginated list (staff/policy) |
| PATCH | `/users/<uuid>/update/` | partial update |
| POST | `/users/<uuid>/password/` | admin set another user’s password |
| GET | `/users/login-events/` | all login events |
| GET | `/users/me/login-events/` | current user’s events |
| GET | `/users/<uuid>/login-events/` | events for one user |

Put static `me` routes **before** `<uuid:id>` routes.

## Health (`core.systems`)

| Method | Path | Auth |
|--------|------|------|
| GET | `/health/` | none |

Probes: database, cache, RabbitMQ (`not_configured` if unset/eager), MinIO (`not_configured` if not default storage). Overall unhealthy → HTTP 503.

## Postman

Collections live under `postman/<app>/`:

- `postman/authentication/authentication_viewset.postman_collection.json`
- `postman/users/users_viewset.postman_collection.json`
- `postman/systems/systems_health_viewset.postman_collection.json`

Set `base_url` to `http://localhost:7000/api/v1`. For health, use `origin_url` (`http://localhost:7000`). Credentials come from `make seed-superuser` / `.secrets.yml` — do not commit passwords.

## OpenAPI

Interactive docs: `/docs/` (requires Django admin login). Schema: `/schema/`.
