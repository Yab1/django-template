#!/usr/bin/env bash
# Fully remove the core.cookbook specimen app from this project.
# Usage:
#   ./scripts/remove_cookbook.sh
#   ./scripts/remove_cookbook.sh --dry-run
#   make remove-cookbook
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DRY_RUN=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help)
      echo "Remove core.cookbook (app, urls, settings, env, postman, styleguide pointers)."
      echo "Usage: $0 [--dry-run]"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] $*"
  else
    eval "$@"
  fi
}

echo "==> Removing cookbook specimen"

# 1. Delete app tree + postman collection (if any).
if [[ -d core/cookbook ]]; then
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] rm -rf core/cookbook"
  else
    rm -rf core/cookbook
    echo "removed core/cookbook/"
  fi
else
  echo "core/cookbook/ already absent"
fi
if [[ -d postman/cookbook ]]; then
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] rm -rf postman/cookbook"
  else
    rm -rf postman/cookbook
    echo "removed postman/cookbook/"
  fi
fi

# 2. Patch Python / env / docs with perl (idempotent).
patch_file() {
  local file="$1"
  shift
  if [[ ! -f "$file" ]]; then
    echo "skip missing $file"
    return 0
  fi
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] patch $file"
    return 0
  fi
  perl -i -0pe "$*" "$file"
  echo "patched $file"
}

# LOCAL_APPS entry
patch_file config/django/base.py '
  s/\n\s*"core\.cookbook\.apps\.CookbookConfig",//g;
'

# URL include block
patch_file core/api/urls.py '
  s/\nfrom django\.conf import settings\n/\n/;
  s/\nif getattr\(settings, "COOKBOOK_ENABLED", True\):\n\s*urlpatterns\.append\(path\("", include\(\("core\.cookbook\.urls", "cookbook"\), namespace="cookbook"\)\)\)\n/\n/;
'

# Settings flag
patch_file config/settings/app.py '
  s/\n# Specimen CRUD app \(Recipe\)\. Off in production if unused\.\nCOOKBOOK_ENABLED = env\.bool\("DJANGO_COOKBOOK_ENABLED", default=True\)\n/\n/;
  s/\nCOOKBOOK_ENABLED = env\.bool\("DJANGO_COOKBOOK_ENABLED", default=True\)\n/\n/;
'

# .env.example / .env
for envf in .env.example .env; do
  patch_file "$envf" '
    s/\n# House style specimen \(`?core\.cookbook`?\)\.[^\n]*\nDJANGO_COOKBOOK_ENABLED=.*\n/\n/;
    s/\nDJANGO_COOKBOOK_ENABLED=.*\n/\n/;
  '
done

# Permission model help text (example code)
patch_file core/security/models/permission.py '
  s/cookbook:recipe:publish/security:role:create/g;
'

# Security migrations help text (cosmetic; optional)
if [[ -f core/security/migrations/0001_initial.py ]]; then
  patch_file core/security/migrations/0001_initial.py '
    s/cookbook:recipe:publish/security:role:create/g;
  '
fi

# Security tests: cookbook codes → security catalog codes that stay registered.
for tf in \
  core/security/tests/services/test_check.py \
  core/security/tests/services/test_role.py \
  core/security/tests/apis/test_role.py
do
  patch_file "$tf" '
    s/cookbook:recipe:publish/security:role:update/g;
    s/cookbook:recipe:create/security:role:create/g;
    s/cookbook:recipe:list_all/security:role:list/g;
    s/cookbook:recipe:list/security:role:list/g;
    s/cookbook:recipe:delete/security:role:delete/g;
    s/cookbook:recipe:get/security:role:get/g;
    s/cookbook:recipe:update/security:role:update/g;
    s/cookbook_author/security_author/g;
    s/cookbook_writer/security_writer/g;
  '
done

# Cursor styleguide / admin: point at users/security when cookbook gone.
if [[ -f .cursor/rules/django-styleguide.mdc ]]; then
  patch_file .cursor/rules/django-styleguide.mdc '
    s/Worked example: core\.cookbook\./Worked example: core.users + URL house verbs (cookbook specimen may be removed)./;
    s/Copy `core\.cookbook\.models\.Recipe`/Copy a domain model that inherits BaseModel + mixins (see Models section)/g;
    s/Copy `core\.cookbook\.admin`/Copy `core.security.admin`/g;
    s/copy cookbook: `apis\/crud\.py` and `apis\/action\.py`/copy users: `apis\/<resource>\/crud.py` (+ `action.py` only for row verbs)/g;
    s/Copy `\*\*`core\.cookbook`\*\*` \(`Recipe`\)\./Copy **`core.users`** (`apis/user/`) for multi-resource layout, and the URL table below for house verbs./;
    s/Copy `\*\*core\.cookbook\*\*` \(`Recipe`\)\./Copy **`core.users`** (`apis/user/`) for multi-resource layout, and the URL table below for house verbs./;
    s/House verbs \(copy `core\.cookbook`\):/House verbs:/;
    s/Tag the view: `authorization_action = "cookbook:recipe:publish"`/Tag the view: `authorization_action = "security:role:create"`/;
    s/cookbook:recipe:list_all/security:role:list/g;
    s/cookbook:recipe:list/users:user:list/g;
    s/Register codes in the app `ready\(\)` via `register_permission` \(copy `core\.cookbook\.permissions`\)\./Register codes in the app `ready()` via `register_permission` (copy `core.security.permissions` or `core.users.permissions_catalog`)./;
    s/Do not put real insurance logic in cookbook\. New domain apps copy its layout, then delete the kitchen nouns\.//;
    s/Several resources in one app copy `core\.parties` \(`apis\/party\/crud\.py`, `apis\/party\/action\.py`\), not one module for the whole app\./Several resources in one app use `apis\/<resource>\/crud.py` (see `core.users`); one resource may use flat `apis\/crud.py` + `apis\/action.py`./;
  '
fi

if [[ -f .cursor/rules/admin-standard.mdc ]]; then
  patch_file .cursor/rules/admin-standard.mdc '
    s/Copy `\*\*`core\.cookbook\.admin`\*\*`\./Copy **`core.security.admin**./;
    s/Copy \*\*`core\.cookbook\.admin`\*\*\./Copy **`core.security.admin`**./;
    s/from core\.cookbook\.models import Recipe\n\nif settings\.COOKBOOK_ENABLED:\n\s*admin\.site\.register\(\[Recipe\]\)/from core.security.models import Permission, Role\n\nadmin.site.register([Permission, Role])/;
    s/description: Django admin — register models, no fat ModelAdmin\. Copy core\.cookbook\.admin\./description: Django admin — register models, no fat ModelAdmin. Copy core.security.admin./;
  '
fi

if [[ -f .cursor/rules/postman-collections.mdc ]]; then
  patch_file .cursor/rules/postman-collections.mdc '
    s/\n\| cookbook \| `postman\/cookbook\/cookbook_viewset\.postman_collection\.json` \|//;
  '
fi

# README / docs one-liners
for doc in README.md docs/index.md docs/architecture/overview.md docs/getting-started.md; do
  [[ -f "$doc" ]] || continue
  if grep -qE '[Cc]ookbook|COOKBOOK' "$doc" 2>/dev/null; then
    patch_file "$doc" '
      s/[Oo]ptional cookbook specimen[^\n]*\n//;
      s/`core\.cookbook`[^\n]*\n//;
      s/DJANGO_COOKBOOK_ENABLED[^\n]*\n//;
    '
  fi
done

echo
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry-run only. Re-run without --dry-run to apply."
  exit 0
fi

echo "Cookbook removed from tree and wiring."
echo "Next:"
echo "  1. Review git diff (esp. security tests + cursor rules)"
echo "  2. make migrate   # Django will unapply cookbook migrations on next migrate if DB had them;"
echo "                   # or: drop cookbook_* tables manually if you need a clean DB"
echo "  3. make test"
echo
echo "Note: existing DBs still have cookbook_* tables until you migrate/drop them."
