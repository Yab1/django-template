# Django Styleguide (HackSoft)

This project follows the **HackSoft Django Styleguide**. Prefer cherry-picking for context, but **must** keep the separation below when writing or changing code.

Full upstream guide: https://github.com/HackSoftware/Django-Styleguide  
Example project: https://github.com/HackSoftware/Django-Styleguide-Example

## Core rule — where logic lives

**Business logic MUST live in:**

- **Services** — writes, side effects (`core/<app>/services.py` or `services/`)
- **Selectors** — reads / queries (`core/<app>/selectors.py` or `selectors/`)
- Model `@property` / methods — only simple, non-relational, cheap derived values
- Model `clean()` — simple multi-field validation on the same model
- DB **constraints** — when the invariant can be expressed in the database

**Business logic MUST NOT live in:**

- APIs / views
- Serializers / forms
- Model `save()`
- Custom managers / querysets (OK for nicer query APIs; not for domain logic)
- Signals (except narrow cache / connect-unrelated cases)

**Property vs selector:** spanning relations or risk of N+1 → **selector**, not `@property`.

Think **core** (services, selectors, models) vs **interface** (APIs, serialization, tasks, management commands).

## Models

- Inherit `core.common.models.BaseModel` when applicable (`id`, `created_at`, `updated_at`, `metadata`).
- Who created / last wrote the row: inherit `AuthorshipMixin` (`created_by`, `updated_by` → `settings.AUTH_USER_MODEL`). Stamp both in the **service** from the authenticated user. Do not declare those FKs by hand. Do not set them in `save()`.
- Call `obj.full_clean()` in the **service** before `save()` (admin forms also call it).
- Prefer `CheckConstraint` / DB constraints for invariants when possible (Django 4.1+ `full_clean` checks constraints).
- Complex / cross-model validation → **service**, not only `clean()`.
- **Do not set `db_table`.** Let Django name the table (`{app_label}_{model}`). Set `db_table` only when that default collides (long M2M intermediary names, a rename you cannot migrate yet). A good specimen is `core.cookbook.models.Recipe` while that app exists — it has no `db_table`.
- **Enums live on the model as nested `TextChoices`.** Do not put status/type values in `constants.py` and do not alias them as `STATUS_DRAFT = "draft"`. Nested name is the field: `class Status(models.TextChoices)`, then `Model.Status.DRAFT` in services, selectors, serializers, filters, tests. `constants.py` is for OpenAPI tags, file-slot keys, and similar non-enum strings.
- **Relations are lazy strings.** Do not import another model in `models.py` to pass it to `ForeignKey` / `OneToOneField` / `ManyToManyField`. Use `"app_label.ModelName"` (or `"self"`). **Exception: the auth user** — `settings.AUTH_USER_MODEL`, never `"users.User"` and never a `User` import. Stops circular imports.

```python
class Recipe(ReferenceIdMixin, VisibleMixin, SoftDeleteMixin, AuthorshipMixin, BaseModel):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    # any non-user relation:
    # category = models.ForeignKey("taxonomy.Category", on_delete=models.PROTECT)

    class Meta:
        verbose_name = _("Recipe")
        verbose_name_plural = _("Recipes")
        ordering = ["-created_at"]
```

## Admin

- One `admin.py`. `admin.site.register([Model, ...])`. New model → append the list.
- No per-model `ModelAdmin`, fieldsets, or `admin/` package on domain apps. Copy `core.security.admin` (or `core.cookbook.admin` while the specimen remains).
- Fat admin allowed only for the auth `User` (`core.users.admin`).

## Services

- Naming: `<entity>_<action>` — e.g. `user_create`, `user_update`, `user_password_change`.
- Prefer **keyword-only** args (`*`) and **type hints**.
- Function-based by default; class-based when you need a namespace / multi-step flow.
- Split `services/` by subdomain when the module grows; re-export from `__init__.py` if useful.
- Updates: use shared `model_update` (when present under `core.common`) for non-side-effect fields; do side effects explicitly in the entity service.

```python
def course_create(*, name: str, start_date: date, end_date: date) -> Course:
    obj = Course(name=name, start_date=start_date, end_date=end_date)
    obj.full_clean()
    obj.save()
    return obj
```

## Selectors

- Naming: same `<entity>_<action>` style — e.g. `user_list`, `login_event_list_for_user`.
- Keyword-only args + type hints.
- Own filtering (e.g. django-filter FilterSet inside the selector). API only validates query params then passes `filters=` into the selector. Drop `None` / `""` / pagination keys before the FilterSet — an invalid FilterSet form returns `qs.none()`.

## APIs & serializers

- **One endpoint per action.** Name: `<Entity><Action>Api` — e.g. `UserListApi`, `UserUpdateApi`.
- Prefer plain `APIView` / project base (`AuthorizedAPIView` when policy + auth required). Avoid fat generic ViewSets that hide logic in serializers.
- Flow: validate input → call service/selector → return `Response(OutputSerializer(...).data, status=...)` from that method. **No business logic in the view. No `Model.objects`, no private query helper, and no function in `apis/` whose job is to build the `Response`.** After a write, reload with the same selector the GET uses so `select_related`, `prefetch_related`, and visibility checks stay in one place. Repeat the selector call and the `return Response(...)` in the method. Do not extract shared render helpers like `_detail_response`.
- **OpenAPI parameters stay on that view.** Write `OpenApiParameter(...)` inside that view's `extend_schema`. Do not assign the parameter to a module constant and import it into another view. Each endpoint owns its own parameter list.
- **File layout.** One resource: `apis/crud.py` and optional `apis/action.py` (row verbs such as `publish`). Several resources in one app: `apis/<resource>/crud.py` — copy `core.users` (`apis/user/`) or `core.security` (`apis/role.py`, `apis/permission.py`). A child resource is its own package, not a verb on the parent. Do not put CRUD and verbs in one flat module when the app has multiple resources.
- **Serializer attributes live on the view**, assigned from the app `serializers/` module. `InputSerializer`, `OutputSerializer`, and `SuccessResponseSerializer = build_success_response_serializer(...)` are class attributes on that one view. Lists also set `class Pagination` (`default_limit=25`, `max_limit=100`), `QuerySerializer` only when the list filters, and `PaginatedResultSerializer`. The method returns the inner payload with `status.HTTP_*`. Do not instantiate `SuccessResponseSerializer` in the method — `EnvelopeJSONRenderer` already wraps it. Do not assign `build_success_response_serializer(...)` to a module constant shared across views. Each view owns its `SuccessResponseSerializer` and its own `component_name`. Specimens: `RecipeCreateApi` in `core.cookbook.apis.crud` (while present) or `UserUpdateApi` in `core.users.apis.user.crud`.
- **Blank line** between the authorization block (`authorization_*`, `parser_classes`) and the serializer block.
- **OpenAPI errors** come from `core.api.schema`. Do not build a local `_ERRORS` dict. A write that can return 409 (domain conflict or idempotency-key reuse) spreads `**OPENAPI_ERRORS`. A write that only raises `ValidationError` spreads `**OPENAPI_VALIDATION_ERRORS`. A read lists only the statuses it returns (`403`, `404`), not either map.
- Dedicated **input** and **output** serializers live in the app `serializers/` module. The view assigns them; it does not declare the field contract inline.
- Prefer `Serializer` over `ModelSerializer` when the contract should stay explicit.
- Nested structures: `inline_serializer` from `core.api.utils`.
- List + pagination: use project helpers (`get_paginated_response`, `LimitOffsetPagination` in `core.api.pagination`).
- GET query serializers: bind `data=request.query_params.dict()`, not the QueryDict. QueryDict looks like HTML form input, so an omitted `BooleanField` becomes `False` and django-filter returns an empty page. Selectors must drop `None` / `""` and ignore `limit` / `offset` (pagination owns those).
- Current user routes: use `/me/` (and `/users/me/...`) before `<uuid:id>` routes.
- Wire apps in `core/api/urls.py` under `/api/v1/`. Infra health stays at `/health/` (not versioned API).

This project wraps 2xx bodies via `EnvelopeJSONRenderer` — views return the **inner** payload; do not double-wrap unless building an error envelope explicitly.

## Idempotency and read cache

- Replay row and `run_idempotent` live in `core.common`. Do not hang them on a product app. Do not add an app for one replay table.
- HTTP replay is `@idempotent(operation="recipe_create")` from `core.api.utils`, next to `@cache_api_response`. Put it on a create and on a command a client retries (`approve`, `publish`, a decision). `required=False` when a missing key must still run. Do not put it on a partial update. A same-key race that can raise `IntegrityError` passes `map_integrity=` from the product service. Same key + same body replays the stored response. Same key + different body is 409.
- File uploads do not use `@idempotent`. The service records the key so a failed replay can delete the blob it already stored.
- Prefer letting domain errors (`ConflictError`, `ServiceError`) bubble to the project exception handler (maps to 409 / status on the error). If an app needs extra mapping, keep a tiny helper next to that app's APIs — do not add `apis/_errors.py` or `call_<app>_service` wrappers that hide the `try` in the view.
- Successful reads use `@cache_api_response(namespace="app:entity")`. The service calls `bust_cache("app:entity")` from `core.common.utils` on commit for every write that changes those responses. Do not cache file downloads.

## Urls

- One URL per API action.
- App `urls.py` + include from `core.api.urls` with a namespace.
- Group by domain; keep list order so static segments (`me`, `create`) win over path converters.
- House verbs:

```text
POST   /<app>/<plural>/create/
GET    /<app>/<plural>/
GET    /<app>/<plural>/<uuid:id>/
DELETE /<app>/<plural>/<uuid:id>/
PATCH  /<app>/<plural>/<uuid:id>/update/
POST   /<app>/<plural>/<uuid:id>/<verb>/   # extra domain action, e.g. publish
```

`GET` and `DELETE` share the resource URL — the HTTP method is the action. Wire both on one view (e.g. `RecipeDetailApi(RecipeGetApi, RecipeDeleteApi)` while cookbook exists). Extra verbs (`publish`) stay `POST …/<verb>/`. `PATCH` stays on `/update/` so the body contract stays explicit.

## Settings

- Django: `config/django/` (`base`, `local`, `production`, `test`).
- Integrations: `config/settings/` (celery, cors, jwt, …), imported from `base.py`.
- Read env via `config.env` / `env`; local `.env`, committed `.env.example`.
- Prefix Django-related vars with `DJANGO_` (e.g. `DJANGO_DEBUG`, `DJANGO_SECRET_KEY`). Do **not** force-prefix integration vars (`CELERY_BROKER_URL`, `SENTRY_DSN`, `MINIO_*`, `AWS_*`).

## Errors

- Use the project exception handler in `core.api` — keep error **envelope** shape consistent with existing APIs.
- Map Django `ValidationError` → DRF validation errors (handler already does this pattern).
- Services raise Django `ValidationError` / domain errors (`ConflictError`, `ServiceError`, `NotFoundError` in `core.common.exceptions`); the handler maps them to HTTP.
- A product conflict (`ConflictError`) is raised in the service, including when `full_clean` reports `code="unique"` and the contract is 409. The view does not catch `IntegrityError`. Prefer bubbling to the handler; optional thin per-app mapper only when needed.
- Do not add `apis/_errors.py`. Do not add `call_<app>_service` whose only job is to wrap the view call in `try`/`except`.
- Do not silence unexpected exceptions (let 500s reach Sentry).

## Celery

- Tasks are an **interface**: fetch data → call a **service**. No business logic in the task body beyond retry/error wiring.
- Import the service **inside** the task function (avoids cycles).
- Import the task at module level with a `_task` suffix when calling from services.
- Trigger with `transaction.on_commit(lambda: some_task.delay(...))` after DB writes.
- Periodic tasks: prefer django-celery-beat; keep schedule definitions explicit (e.g. setup command) when added.

## Testing

- Prefer testing **services** and **selectors** (they hold the domain).
- Service tests **hit the DB**; mock Celery / external I/O.
- Layout: `core/<app>/tests/{services,selectors,models,apis}/test_<name>.py`.
- Factories (`factory_boy`) or `Model.objects.create()` / other services for setup.
- Grant catalog codes in tests with `grant_permissions` from `core.security.testing`.

## Code placement (this repo)

| Kind | Location |
|------|----------|
| DRF helpers (serializers utils, envelope, pagination) | `core/api/` |
| Shared non-API helpers | `core/common/` |
| Writes | `core/<app>/services/` |
| Reads | `core/<app>/selectors/` |
| REST endpoints | `core/<app>/apis/` (+ `urls.py`) |
| Models | `core/<app>/models/` |
| Admin | `core/<app>/admin.py` (see `admin-standard`) |

When unsure: **API-only** → `core/api/`; **shared** → `core/common/`; **domain write/read** → app services/selectors.

Idempotency row, runner, `ConflictError`, and `bust_cache` stay in `core.common`. The idempotency decorator, the response-cache decorator, `OPENAPI_ERRORS`, and `OPENAPI_VALIDATION_ERRORS` stay in `core.api`.

## Authorization

Product APIs check **permission codes**, never role names, never `is_staff`.

- Register codes in the app `ready()` via `register_permission` (copy `core.security.permissions` or `core.users.permissions_catalog`; cookbook has the same pattern while present).
- Tag the view: `authorization_action = "security:role:create"`. Combined GET+DELETE: `authorization_actions = {"GET": "...get", "DELETE": "...delete"}`.
- Directory code and own code on the same URL: `authorization_action_any = ("app:entity:list_all", "app:entity:list")`. `PolicyPermission` uses the first code the caller holds. Do not add `get_authorization_action` that calls `user_has_permission`.
- Superuser bypasses. Untagged views stay authenticated-only (`/me`, inbox).
- Row visibility stays in selectors (e.g. list-all vs own rows). Do not hang product ACL on Django Groups, `auth.Permission`, or Guardian.
- Roles are data (bags of codes). Permission codes are owned by code.

## Worked example

While **`core.cookbook`** (`Recipe`) is in the tree, it is the house specimen — not a product module. It shows `BaseModel` + mixins (`AuthorshipMixin`), nested `TextChoices`, no `db_table`, service/selector split, explicit serializers on the view, one URL per action (CRUD + `publish`), django-filter, thin admin, files slot, and catalog permission tags.

After `make remove-cookbook`, copy **`core.users`** (`apis/user/`) for multi-resource layout and **`core.security`** for roles/permissions APIs. Keep the URL house-verb table above.

New domain apps: copy that layout, then replace the specimen nouns with your domain.
