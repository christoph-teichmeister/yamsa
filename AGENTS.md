# Repository Guidelines

## Project Structure & Module Organization
The project is a Django monolith rooted at `manage.py`. Domain-specific logic lives inside `apps/`, e.g. `apps/transaction`, `apps/room`, and `apps/account`; each app contains its own `models`, `views`, `templates`, and `tests`. Shared templates and assets belong in `apps/templates` and `static/`, while compiled artefacts land in `staticfiles/`. Developer tooling scripts sit in `scripts/` and container assets in `Dockerfile`, `docker-compose.yml`, and `entrypoint.sh`. Documentation, including AI prompt history, lives in `docs/`.

## Build, Test, and Development Commands
- `pipenv install --dev` — install Python 3.12 dependencies including tooling.
- `pipenv run python manage.py migrate` — apply schema changes before running the app.
- `pipenv run python manage.py runserver 0.0.0.0:8000` — local dev server with HTMX/Bootstrap UI.
- `pipenv run python manage.py test` — execute Django test suite under the default settings module.
- `docker exec yamsa_backend python manage.py test apps` — run the full suite inside the backend container (host Pipenv Python lacks `_sqlite3`, so containerized Python 3.11 is required for reliable test runs).
- `pipenv run coverage run manage.py test && pipenv run coverage report` — generate coverage (config in `pyproject.toml`).
- `docker-compose up --build` — parity environment that mirrors the production container image.

## Coding Style & Naming Conventions
Follow Python’s 4-space indentation and keep modules typed where practical. Use `snake_case` for functions, `PascalCase` for classes, and `SCREAMING_SNAKE_CASE` for settings. Run `pipenv run ruff check --fix .` before committing; it handles import order, linting, and selected auto-fixes. Templates must pass `pipenv run djlint apps --reformat`; lean on Bootstrap 5 utility classes (`d-flex`, `px-2`, `gap-2`, etc.) and HTMX attributes instead of custom CSS whenever possible. Keep static JS modular inside `static/js/` and co-locate SCSS/CSS with the component it styles.

## Testing Guidelines
Place tests beside their apps under `apps/*/tests/` using `test_<unit>.py` naming. Prefer Django’s `TestCase`/`TransactionTestCase` plus `pytest`-style assertions for clarity. Aim for coverage parity with existing badges (>85%); add regression tests when touching business-critical flows such as settlement math or transaction rendering. Use factories or fixtures over ad-hoc object creation to keep tests deterministic.

## Commit & Pull Request Guidelines
History follows Conventional Commits (`feat: add split animation`, `fix: correct room balance`). Keep messages in the imperative and scoped to a single concern. Every PR should: describe the change and rationale, link the related issue, list validation commands (`manage.py test`, linters), and attach before/after screenshots or GIFs for UI tweaks (especially mobile layouts). Request review only after CI passes locally to reduce churn.

## Security & Configuration Tips
Secrets belong in environment variables or `.env` files excluded from git; never hard-code keys for mail, web push, or third-party APIs. Use `config/settings/*` to separate local vs. production configs, and prefer feature flags/settings constants over inline literals when adding new toggles.
