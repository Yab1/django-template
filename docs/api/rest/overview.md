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
| GET | `/users/` | paginated list (`users:user:list`) |
| PATCH | `/users/<uuid>/update/` | partial update |
| POST | `/users/<uuid>/password/` | admin set another user’s password |
| GET | `/users/login-events/` | all login events |
| GET | `/users/me/login-events/` | current user’s events |
| GET | `/users/<uuid>/login-events/` | events for one user |

Put static `me` routes **before** `<uuid:id>` routes.

## Security (`core.security`)

Permission catalog and roles. Check **codes**, never role names. Superuser bypasses every tagged view.

| Method | Path | Perm |
|--------|------|------|
| GET | `/security/me/permissions/` | authenticated |
| GET | `/security/me/roles/` | authenticated |
| GET | `/security/permissions/` | `security:permission:list` |
| GET | `/security/permissions/<uuid>/` | `security:permission:get` |
| POST | `/security/roles/create/` | `security:role:create` |
| GET | `/security/roles/` | `security:role:list` |
| GET | `/security/roles/<uuid>/` | `security:role:get` |
| PATCH | `/security/roles/<uuid>/update/` | `security:role:update` |
| DELETE | `/security/roles/<uuid>/` | `security:role:delete` |
| GET | `/security/users/<uuid>/roles/` | `security:user_role:list` |
| POST | `/security/users/<uuid>/roles/assign/` | `security:user_role:assign` |
| POST | `/security/users/<uuid>/roles/<uuid>/revoke/` | `security:user_role:revoke` |

Permission codes are registered in app `ready()` (copy cookbook / users / files / notifications catalogs). Roles attach those codes. Synced into `security.Permission` on `post_migrate`. Django Groups remain admin-only. Gate with `DJANGO_PERMISSIONS_ENABLED` (`.env.example` defaults `false` for local).

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

Set `base_url` to `http://localhost:8000/api/v1`. For health, use `origin_url` (`http://localhost:8000`). Credentials come from `make seed-superuser` / `.secrets.yml` — do not commit passwords.

## OpenAPI

Interactive docs: `/docs/` (requires Django admin login). Schema: `/schema/`.
