# Repository Guidelines

## Project Structure & Module Organization

The project is a Django monolith rooted at `manage.py`. Domain-specific logic lives inside `apps/`, e.g.
`apps/transaction`, `apps/room`, and `apps/account`; each app contains its own `models`, `views`, `templates`, and
`tests`. Shared templates and assets belong in `apps/templates` and `static/`, while compiled artefacts land in
`staticfiles/`. Developer tooling scripts sit in `scripts/` and container assets in `Dockerfile`, `docker-compose.yml`,
and `entrypoint.sh`. Documentation, including AI prompt history, lives in `docs/`.

## Build, Test, and Development Commands

- All Django/manage.py invocations must run inside the `yamsa_backend` Docker container (e.g.
  `docker exec yamsa_backend python manage.py <cmd>`) because the host environment lacks the necessary dependencies.
  Agents should feel free to execute any needed commands inside the containers without repeatedly asking for
  confirmation.
- `uv sync --all-extras --no-install-project` - install Python 3.12 dependencies including tooling.
- `uv run python manage.py migrate` - apply schema changes before running the app.
- `uv run python manage.py runserver 0.0.0.0:8000` - local dev server with HTMX/Bootstrap UI.
- `uv run python manage.py test` - execute Django test suite under the default settings module.
- `docker exec yamsa_backend python manage.py test apps` - run the full suite inside the backend container (host Pipenv
  Python lacks `_sqlite3`, so containerized Python 3.11 is required for reliable test runs).
- `uv run coverage run manage.py test && uv run coverage report` - generate coverage (config in
  `pyproject.toml`).
- `docker-compose up --build` - parity environment that mirrors the production container image.

## Coding Style & Naming Conventions

Follow Python’s 4-space indentation and keep modules typed where practical. Use `snake_case` for functions, `PascalCase`
for classes, and `SCREAMING_SNAKE_CASE` for settings. Run `uv run ruff check --fix .` before committing; it handles
import order, linting, and selected auto-fixes. Templates must pass `uv run djlint apps --reformat`; lean on
Bootstrap 5 utility classes (`d-flex`, `px-2`, `gap-2`, etc.) and HTMX attributes instead of custom CSS whenever
possible. Keep static JS modular inside `static/js/` and co-locate SCSS/CSS with the component it styles. **Edit
canonical static assets under `apps/static/…` (e.g., `apps/static/js/navigation.js`) and let hashed copies
in `static/`/`staticfiles/` be generated artifacts.**

## Design System & UI Concepts

- Bootstrap 5 provides the base; lean on utility classes, cards, badges, and offcanvas components before reaching for
  custom CSS.
- Layouts should feel airy: use `container` + responsive padding (`px-2 px-md-4 px-lg-5`), `rounded-4` cards, and
  `shadow-sm`/`shadow` for emphasis.
- Primary CTAs are full-width or paired buttons with icons (`bi` set) and consistent spacing (`gap-2`). Avoid duplicate
  actions; prefer a single, well-labeled button per task.
- Content blocks typically use stacked cards or responsive grids (`row g-4`) so desktop and mobile share the same
  markup.
- Keep typography calm: headings use `fw-semibold`, supportive text uses `text-muted` small copy; badge colors convey
  status (e.g., `text-bg-dark` for elevated roles).
- When using HTMX, ensure loaders target `#body`, and actions that mimic navigation also manage scroll restoration (see
  `apps/static/js/navigation.js`).

## Testing Guidelines

Place tests beside their apps under `apps/*/tests/` using `test_<unit>.py` naming. Prefer Django’s `TestCase`/
`TransactionTestCase` plus `pytest`-style assertions for clarity. Aim for coverage parity with existing badges (>85%);
add regression tests when touching business-critical flows such as settlement math or transaction rendering. Use
factories or fixtures over ad-hoc object creation to keep tests deterministic.

## Commit & Pull Request Guidelines

History follows Conventional Commits (`feat: add split animation`, `fix: correct room balance`). Keep messages in the
imperative and scoped to a single concern. Every PR should: describe the change and rationale, link the related issue,
list validation commands (`manage.py test`, linters), and attach before/after screenshots or GIFs for UI tweaks (
especially mobile layouts). Request review only after CI passes locally to reduce churn.

## Security & Configuration Tips

Secrets belong in environment variables or `.env` files excluded from git; never hard-code keys for mail, web push, or
third-party APIs. Use `config/settings/*` to separate local vs. production configs, and prefer feature flags/settings
constants over inline literals when adding new toggles.

## Pull Request Review Workflow

When responding to a review you've left on a pull request, use the GitHub MCP APIs to enumerate the review comments and
write them to a markdown file inside the top-level `.pull-requests` directory. Convert each comment into an actionable
task description so it can later be fed back to you for implementation. After creating that file, perform the requested
analysis or edits, then post replies to the original pull-request comments that explain what you did to address each
comment—prefix every reply with `AI:`. Once the replies are posted and there is no further need for the intermediate
notes, delete the markdown file from `.pull-requests`.
