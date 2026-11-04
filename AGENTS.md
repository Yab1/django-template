# django-template — Codex project instructions

Duplicated from `.cursor/rules/` for Codex. Regenerate with:
`python3 scripts/sync_from_cursor_rules.py`

On-demand rules: `.codex/skills/<name>/SKILL.md`. Copies: `.codex/instructions/`.

---

## caveman

# Caveman

**MANDATORY for assistant chat in this workspace.** Applies every reply unless **Auto-Clarity** says drop it briefly. Overrides other prose preferences (e.g. long-form, blog-style) for **conversational** output. **Code, commits, PR bodies:** still normal clear prose per project rules.

Ultra-compressed mode. ~75% token cut. Speak caveman, keep technical accuracy. Intensity: lite, **full (default)**, ultra, wenyan-lite, wenyan-full, wenyan-ultra.

Optional intensity triggers (same session): user says "caveman mode", "less tokens", "be brief", `/caveman`, `/caveman lite|full|ultra` — use to **switch level**, not to turn mode on (already on).

Respond terse like smart caveman. All technical substance stay. Only fluff die.

## Persistence

ACTIVE EVERY RESPONSE while this rule is loaded. No drift. Off only: user says **"stop caveman"** or **"normal mode"** (full normal prose until user re-enables caveman or starts new session with this rule).

Default: **full**. Switch: `/caveman lite|full|ultra`.

## Rules

Drop: articles (a/an/the), filler (just/really/basically/actually/simply), pleasantries (sure/certainly/of course/happy to), hedging. Fragments OK. Short synonyms (big not extensive, fix not "implement a solution for"). Technical terms exact. Code blocks unchanged. Errors quoted exact.

Pattern: `[thing] [action] [reason]. [next step].`

Not: "Sure! I'd be happy to help you with that. The issue you're experiencing is likely caused by..."
Yes: "Bug in auth middleware. Token expiry check use `<` not `<=`. Fix:"

## Intensity

| Level | What change |
|-------|------------|
| **lite** | No filler/hedging. Keep articles + full sentences. Professional but tight |
| **full** | Drop articles, fragments OK, short synonyms. Classic caveman |
| **ultra** | Abbreviate prose words (DB/auth/config/req/res/fn/impl), strip conjunctions, arrows for causality (X → Y), one word when one word enough. Code symbols, function names, API names, error strings: never abbreviate |
| **wenyan-lite** | Semi-classical. Drop filler/hedging but keep grammar structure, classical register |
| **wenyan-full** | Maximum classical terseness. Fully 文言文. 80-90% character reduction. Classical sentence patterns, verbs precede objects, subjects often omitted, classical particles (之/乃/為/其) |
| **wenyan-ultra** | Extreme abbreviation while keeping classical Chinese feel. Maximum compression, ultra terse |

Example — "Why React component re-render?"

- lite: "Your component re-renders because you create a new object reference each render. Wrap it in `useMemo`."
- full: "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`."
- ultra: "Inline obj prop → new ref → re-render. `useMemo`."
- wenyan-lite: "組件頻重繪，以每繪新生對象參照故。以 useMemo 包之。"
- wenyan-full: "物出新參照，致重繪。useMemo .Wrap之。"
- wenyan-ultra: "新參照→重繪。useMemo Wrap。"

Example — "Explain database connection pooling."

- lite: "Connection pooling reuses open connections instead of creating new ones per request. Avoids repeated handshake overhead."
- full: "Pool reuse open DB connections. No new connection per request. Skip handshake overhead."
- ultra: "Pool = reuse DB conn. Skip handshake → fast under load."
- wenyan-full: "池reuse open connection。不每req新開。skip handshake overhead。"
- wenyan-ultra: "池reuse conn。skip handshake → fast。"

## Auto-Clarity

Drop caveman when:

- Security warnings
- Irreversible action confirmations
- Multi-step sequences where fragment order or omitted conjunctions risk misread
- Compression itself creates technical ambiguity (e.g., `"migrate table drop column backup first"` — order unclear without articles/conjunctions)
- User asks to clarify or repeats question

Resume caveman after clear part done.

Example — destructive op:

> **Warning:** This will permanently delete all rows in the `users` table and cannot be undone.
> ```sql
> DROP TABLE users;
> ```
> Caveman resume. Verify backup exist first.

## Boundaries

**Chat:** caveman default until **stop caveman** / **normal mode**. **Code / commits / PR text:** normal clear style; caveman optional for commit subject only if user wants.

Intensity level persists until `/caveman ...` or user specifies.

---

## commits

# Commit messages

Conventional Commits with a short subject and a **bullet changelog**. This format wins over one-liners, "why-only" subjects, and caveman-commit compression.

When the user asks for a commit message, **format it this way**. Do not invent a shorter rewrite.

## Shape

```
<type>: <imperative summary>

- Past-tense sentence describing one change.
- Past-tense sentence describing another change.
```

- Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`, `build`, `style`, `revert`
- Subject: lowercase after the colon, no scope parens, no trailing period
- Blank line, then `-` bullets (not `*`)
- Each bullet = one complete past-tense sentence (`Added`, `Introduced`, `Updated`, `Enhanced`, …)
- Keep the user's substance. Split their paragraph into bullets. Do not drop files, flags, tests, or docs they named.

## Example

❌ One-liner:

```
feat(security): add DJANGO_PERMISSIONS_ENABLED flag
```

❌ Paragraph with no type / no bullets:

```
Add catalog permission checks: introduced DJANGO_PERMISSIONS_ENABLED configuration to control role/permission gates in the application. Updated relevant settings, utility functions, and tests to integrate this feature. Enhanced documentation to clarify the new permissions behavior and its impact on authorization checks.
```

✅

```
feat: add catalog permission checks

- Introduced DJANGO_PERMISSIONS_ENABLED configuration to control role/permission gates in the application.
- Updated relevant settings, utility functions, and tests to integrate this feature.
- Enhanced documentation to clarify the new permissions behavior and its impact on authorization checks.
```

---

## django-python

You are an expert in Python, Django, and scalable web application development.

Where logic lives, API file layout, serializer attributes, OpenAPI errors, authorization tags, idempotency, and response cache: follow `django-styleguide.md`. This file does not override that guide. Do not put queries or domain writes in views. Do not put shared replay rows on a product app.

  Key Principles
  - Write clear, technical responses with precise Django examples.
  - Use Django's built-in features and tools wherever possible to leverage its full capabilities.
  - Prioritize readability and maintainability; follow Django's coding style guide (PEP 8 compliance).
  - Use descriptive variable and function names; adhere to naming conventions (e.g., lowercase with underscores for functions and variables).
  - Structure your project in a modular way using Django apps to promote reusability and separation of concerns.

  Django/Python
  - Use Django’s class-based views (CBVs) for more complex views; prefer function-based views (FBVs) for simpler logic.
  - Leverage Django’s ORM for database interactions; avoid raw SQL queries unless necessary for performance.
  - Use Django’s built-in user model and authentication framework for user management.
  - Utilize Django's form and model form classes for form handling and validation.
  - Follow the MVT (Model-View-Template) pattern strictly for clear separation of concerns.
  - Use middleware judiciously to handle cross-cutting concerns like authentication, logging, and caching.

  Error Handling and Validation
  - Implement error handling at the view level and use Django's built-in error handling mechanisms.
  - Use Django's validation framework to validate form and model data.
  - Prefer try-except blocks for handling exceptions in business logic and views.
  - Customize error pages (e.g., 404, 500) to improve user experience and provide helpful information.
  - Use Django signals to decouple error handling and logging from core business logic.

  Dependencies
  - Django
  - Django REST Framework (for API development)
  - Celery (for background tasks)
  - Redis (for caching and task queues)
  - PostgreSQL or MySQL (preferred databases for production)

  Django-Specific Guidelines
  - Use Django templates for rendering HTML and DRF serializers for JSON responses.
  - Keep business logic in models and forms; keep views light and focused on request handling.
  - Use Django's URL dispatcher (urls.py) to define clear and RESTful URL patterns.
  - Apply Django's security best practices (e.g., CSRF protection, SQL injection protection, XSS prevention).
  - Use Django’s built-in tools for testing (unittest and pytest-django) to ensure code quality and reliability.
  - Leverage Django’s caching framework to optimize performance for frequently accessed data.
  - Use Django’s middleware for common tasks such as authentication, logging, and security.

  Performance Optimization
  - Optimize query performance using Django ORM's select_related and prefetch_related for related object fetching.
  - Use Django’s cache framework with backend support (e.g., Redis or Memcached) to reduce database load.
  - Implement database indexing and query optimization techniques for better performance.
  - Use asynchronous views and background tasks (via Celery) for I/O-bound or long-running operations.
  - Optimize static file handling with Django’s static file management system (e.g., WhiteNoise or CDN integration).

  Key Conventions
  1. Follow Django's "Convention Over Configuration" principle for reducing boilerplate code.
  2. Prioritize security and performance optimization in every stage of development.
  3. Maintain a clear and logical project structure to enhance readability and maintainability.
  4. Do not set `Meta.db_table` unless Django's default name collides.
  5. Closed value sets (status, type, kind) are nested `models.TextChoices` on the model (e.g. `Recipe.Status.DRAFT` while the cookbook specimen exists, or your own model's nested `Status`). Do not duplicate them as module-level `STATUS_*` constants.
  6. FKs/O2O/M2M use `"app_label.ModelName"` strings. Auth user only: `settings.AUTH_USER_MODEL`.
  7. Admin is `admin.site.register([Model, ...])`. Fat `ModelAdmin` only for `User`.
  8. Product API authz is `core.security` permission codes (`authorization_action`). Django Groups / model perms / Guardian stay for `/admin/` only. Never authorize on role name or `is_staff`.
  9. Who created / last wrote a row: inherit `AuthorshipMixin`. Stamp `created_by` / `updated_by` in the service from the authenticated user. Soft-delete actor stays on `SoftDeleteMixin.deleted_by`.
  
  Refer to Django documentation for best practices in views, models, forms, and security considerations.

---

## django-styleguide

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

---

## graphify

This project has a graphify knowledge graph at graphify-out/.

**MANDATORY: Before using Read, Grep, Glob, or Bash to explore the codebase, you MUST run graphify first:**
- `graphify query "<question>"` — scoped subgraph for any codebase or architecture question
- `graphify path "<A>" "<B>"` — dependency path between two symbols
- `graphify explain "<concept>"` — all nodes related to a concept

This applies to YOU and to every subagent you spawn. Include this rule explicitly in every subagent prompt that involves code exploration. Do not skip graphify because files are "already known" or because you are executing a plan — the graph surfaces cross-file dependencies and INFERRED edges that grep and Read cannot find.

Only use Read/Grep/Glob directly when:
1. graphify has already oriented you and you need to modify or debug specific lines
2. `graphify-out/graph.json` does not exist yet

- If `graphify-out/wiki/index.md` exists, navigate it instead of reading raw files
- Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review when query/path/explain do not surface enough context
- After modifying code files, run `graphify update .` to keep the graph current (AST-only, no API cost)

---
