# Contributing

This doc is for **everyone working on the repo** (proprietary project, multiple collaborators). It covers setup, workflow, and what to do before opening a PR.

---

## Onboarding checklist (before your first PR)

- [ ] **Clone** the repo and open it in your editor.
- [ ] **Install dependencies and hooks:** run `make update` (or at least `make install` then `make precommit`). This installs Git hooks so the pre-push hook blocks direct push to `main` and pre-commit runs lint on commit.
- [ ] **Copy env:** copy `.env.example` to `.env` and set required variables (see README).
- [ ] **Verify setup:** run `make lint` and `make test`. Both should pass.
- [ ] **Read the docs:** skim [docs/README.md](docs/README.md) and [docs/conventions/code_organization.md](docs/conventions/code_organization.md). Use the [style guide](docs/conventions/style_guide.md) for code structure (services, selectors, APIs, etc.).
- [ ] **Create a branch** from `main` for your work. Do not push directly to `main` (the pre-push hook will block it).

---

## Workflow

1. **Branch from `main`:**  
   `git checkout main && git pull && git checkout -b your-feature-name`

2. **Make changes** following the [style guide](docs/conventions/style_guide.md) and [code organization](docs/conventions/code_organization.md).

3. **Run locally before pushing:**  
   `make lint` and `make test`. Fix any failures.

4. **Commit:**  
   Pre-commit will run Ruff (check + format). Write clear commit messages (e.g. `feat: add X`, `fix: Y`).

5. **Push your branch** and open a **pull request** against `main`. Fill in the PR template (description, how to test, etc.).

6. **CI** runs lint and tests on the PR. Fix any failures. Once the PR is approved and CI is green, maintainers will merge (typically with “Squash and merge” so `main` gets one commit per PR).

---

## Where to put code

- **Business logic (writes):** `core/<app>/services.py` or `core/common/services/`
- **Read-only queries:** `core/<app>/selectors.py`
- **REST endpoints:** `core/<app>/apis.py`, wired in `core/api/urls.py`
- **Models:** `core/<app>/models.py`
- **DRF-only helpers:** `core/api/utils/`
- **Shared/generic helpers:** `core/common/utils/`

See [docs/conventions/code_organization.md](docs/conventions/code_organization.md) for the full table and [docs/conventions/style_guide.md](docs/conventions/style_guide.md) for the full style guide.

---

## Useful commands

| Command | Description |
| -------- | ------------- |
| `make help` | List all Make targets |
| `make update` | Full setup (deps, migrate, pre-commit, submodules, etc.) |
| `make precommit` | Install Git hooks + pre-commit hooks |
| `make lint` | Run Ruff and pre-commit checks |
| `make test` | Run pytest |
| `make test-cov` | Run tests with coverage report |
| `make create-app APP=<name>` | Create a new Django app under `core/` |
| `make audit` | Run dependency/security audit (pip-audit) |

---

## Questions

- **Code style and structure:** [docs/conventions/style_guide.md](docs/conventions/style_guide.md) and [docs/conventions/code_organization.md](docs/conventions/code_organization.md)
- **Where to document something:** [docs/README.md](docs/README.md)
- **Contact:** see the [README](README.md#contact) for maintainer and organization details.
