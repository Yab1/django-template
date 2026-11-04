#!/usr/bin/env bash
# Rename template identity tokens for a new project clone.
# Usage:
#   ./scripts/rename_project.sh --snake acme_api --kebab acme-api --name "Acme API" --prefix AC
#   ./scripts/rename_project.sh ... --dry-run
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SNAKE=""
KEBAB=""
DISPLAY=""
PREFIX=""
DRY_RUN=0

usage() {
  cat <<'EOF'
Rename django-template identity strings for a new project.

Required:
  --snake   <slug>   snake_case  (compose, celery, containers)  e.g. acme_api
  --kebab   <slug>   kebab-case  (pyproject, APP_NAME, buckets) e.g. acme-api
  --name    <text>   display name (docs, swagger)               e.g. "Acme API"
  --prefix  <2-4>    reference-id platform prefix               e.g. AC

Optional:
  --dry-run          print planned changes; write nothing
  -h, --help         show this help

Examples:
  ./scripts/rename_project.sh --snake acme_api --kebab acme-api --name "Acme API" --prefix AC --dry-run
  ./scripts/rename_project.sh --snake acme_api --kebab acme-api --name "Acme API" --prefix AC
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --snake) SNAKE="${2:-}"; shift 2 ;;
    --kebab) KEBAB="${2:-}"; shift 2 ;;
    --name) DISPLAY="${2:-}"; shift 2 ;;
    --prefix) PREFIX="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$SNAKE" || -z "$KEBAB" || -z "$DISPLAY" || -z "$PREFIX" ]]; then
  echo "Missing required args." >&2
  usage >&2
  exit 2
fi

if [[ ! "$SNAKE" =~ ^[a-z][a-z0-9_]*$ ]]; then
  echo "--snake must be lowercase snake_case starting with a letter." >&2
  exit 2
fi
if [[ ! "$KEBAB" =~ ^[a-z][a-z0-9-]*$ ]]; then
  echo "--kebab must be lowercase kebab-case starting with a letter." >&2
  exit 2
fi
if [[ ! "$PREFIX" =~ ^[A-Z][A-Z0-9]{1,3}$ ]]; then
  echo "--prefix must be 2–4 chars, uppercase letters/digits, start with a letter (e.g. AC, DT, ACM)." >&2
  exit 2
fi

# Paths to skip (never rewrite).
prune_args=(
  -path './.git' -o
  -path './.venv' -o
  -path './venv' -o
  -path './node_modules' -o
  -path './graphify-out' -o
  -path './htmlcov' -o
  -path './.mypy_cache' -o
  -path './.pytest_cache' -o
  -path './.ruff_cache' -o
  -path './uv.lock' -o
  -name '*.pyc' -o
  -name '*.pyo' -o
  -name '*.so' -o
  -name '*.png' -o
  -name '*.jpg' -o
  -name '*.jpeg' -o
  -name '*.gif' -o
  -name '*.webp' -o
  -name '*.pdf' -o
  -name '*.woff*' -o
  -name '*.ttf' -o
  -name '*.ico'
)

# Text-ish extensions + extensionless known scripts.
is_text_file() {
  local f="$1"
  case "$f" in
    *.py|*.md|*.mdc|*.txt|*.toml|*.yml|*.yaml|*.sh|*.env|*.example|*.conf|*.ini|*.cfg|*.json|*.html|*.css|*.js|*.ts|*.tsx|*.sql|*.mk|Makefile|Dockerfile*|Jenkinsfile*)
      return 0 ;;
  esac
  # .env without extension
  case "$(basename "$f")" in
    .env|.env.*|Makefile|Dockerfile|Jenkinsfile|Procfile) return 0 ;;
  esac
  return 1
}

# Longest-first so django_template wins before accidental short matches.
# Order matters inside perl.
apply_replacements() {
  local file="$1"
  # Use \Q...\E style via quotemeta in perl args.
  perl -i -0pe '
    BEGIN {
      $snake = $ENV{RP_SNAKE};
      $kebab = $ENV{RP_KEBAB};
      $display = $ENV{RP_DISPLAY};
      $prefix = $ENV{RP_PREFIX};
    }
    # Display phrases first (contain spaces).
    s/Django Template API/${display} API/g;
    s/REST API for Django Template\./REST API for ${display}./g;
    s/Django Template Documentation/${display} Documentation/g;
    s/Django Template/${display}/g;

    # Kebab identity.
    s/django-template-entrypoint/${kebab}-entrypoint/g;
    s/django-template-media/${kebab}-media/g;
    s/django-template-static/${kebab}-static/g;
    s/django-template-password-validator/${kebab}-password-validator/g;
    s/django-template/${kebab}/g;

    # Snake identity (containers, queues, nets).
    s/django_template_gunicorn/${snake}_gunicorn/g;
    s/django_template_infra/${snake}_infra/g;
    s/django_template/${snake}/g;

    # Platform prefix (word-ish; keep model entity prefixes like RCP).
    s/\bDT-/${prefix}-/g;
    s/default="DT"/default="${prefix}"/g;
    s/default=\"DT\"/default=\"${prefix}\"/g;
    s/REFERENCE_ID_PLATFORM_PREFIX=DT/REFERENCE_ID_PLATFORM_PREFIX=${prefix}/g;
    s/\(DT for /\(${prefix} for /g;
    s/e\.g\. DT-/e.g. ${prefix}-/g;
    s/prefix \(DT\)/prefix (${prefix})/g;
  ' "$file"
}

export RP_SNAKE="$SNAKE" RP_KEBAB="$KEBAB" RP_DISPLAY="$DISPLAY" RP_PREFIX="$PREFIX"

mapfile -d '' FILES < <(
  find . \( "${prune_args[@]}" \) -prune -o -type f -print0
)

changed=0
planned=0
for f in "${FILES[@]}"; do
  f="${f#./}"
  [[ -z "$f" ]] && continue
  is_text_file "$f" || continue
  # Skip this script itself while dry-running identity tokens inside comments is fine;
  # but never rewrite the rename script's own source tokens used as search keys.
  [[ "$f" == "scripts/rename_project.sh" ]] && continue

  if ! grep -Iq . "$f" 2>/dev/null; then
    continue
  fi

  if ! grep -qE 'django_template|django-template|Django Template|\bDT-|=DT\b|default="DT"|PLATFORM_PREFIX=DT' "$f" 2>/dev/null; then
    continue
  fi

  planned=$((planned + 1))
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[dry-run] $f"
    continue
  fi

  cp "$f" "$f.rename_bak"
  apply_replacements "$f"
  if cmp -s "$f" "$f.rename_bak"; then
    rm -f "$f.rename_bak"
  else
    rm -f "$f.rename_bak"
    echo "updated  $f"
    changed=$((changed + 1))
  fi
done

echo
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry-run: $planned file(s) would change."
  echo "Snake=$SNAKE kebab=$KEBAB name=$DISPLAY prefix=$PREFIX"
  exit 0
fi

echo "Updated $changed file(s)."

# Leftover scan (ignore this script + lock).
leftovers="$(
  find . \( "${prune_args[@]}" \) -prune -o -type f -print0 |
  xargs -0 grep -lE 'django_template|django-template|Django Template' 2>/dev/null |
  grep -vE '^(scripts/rename_project\.sh|uv\.lock)$' || true
)"
if [[ -n "$leftovers" ]]; then
  echo
  echo "WARNING: leftover identity tokens still present in:"
  echo "$leftovers"
  echo "Inspect and fix manually (or re-run after adjusting skip lists)."
fi

if command -v uv >/dev/null 2>&1; then
  echo
  echo "Regenerating uv.lock for new package name..."
  uv lock
fi

echo
echo "Done. Next:"
echo "  1. Review git diff"
echo "  2. Copy .env.example → .env if needed"
echo "  3. make infra-up && make migrate"
echo "  4. Optional: make remove-cookbook   # drop specimen app"
