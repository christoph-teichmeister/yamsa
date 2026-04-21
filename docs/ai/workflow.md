# Workflow

## Build, Test, and Development Commands

- All Django/manage.py invocations must run inside the local `uv shell` (e.g. start it via `uv shell` and then run
  `python manage.py <cmd>`) so you benefit from the pinned Python 3.11.11 environment. Agents are always allowed to
  open the uv shell and run commands there without asking for extra permission; no Docker-based workflows are required.
- `uv sync --all-extras --no-install-project` — install Python 3.11.11 dependencies including tooling.
- `uv run python manage.py migrate` — apply schema changes before running the app.
- `uv run python manage.py runserver 0.0.0.0:8000` — local dev server with HTMX/Bootstrap UI.
- `uv run pytest` — execute Django test suite via pytest under the default settings module.
- `uv run coverage run -m pytest && uv run coverage report` — generate coverage (config in `pyproject.toml`).

## Commit & Pull Request Guidelines

History follows Conventional Commits (`feat: add split animation`, `fix: correct room balance`). Keep messages in the
imperative and scoped to a single concern. Every PR should: describe the change and rationale, link the related issue,
list validation commands (`uv run pytest`, linters), and attach before/after screenshots or GIFs for UI tweaks
(especially mobile layouts). Request review only after CI passes locally to reduce churn.

PR titles follow the pattern `#<issue>: <Short description>` in sentence case, e.g. `#333: Fix second transaction
failing after first`.

## Pull Request Review Workflow

When responding to a review you've left on a pull request, use the GitHub MCP APIs to enumerate the review comments and
write them to a markdown file inside the top-level `.pull-requests` directory. Convert each comment into an actionable
task description so it can later be fed back to you for implementation. After creating that file, perform the requested
analysis or edits, then post replies to the original pull-request comments that explain what you did to address each
comment — prefix every reply with `AI:`. Once the replies are posted and there is no further need for the intermediate
notes, delete the markdown file from `.pull-requests`.

## Security & Configuration Tips

Secrets belong in environment variables or `.env` files excluded from git; never hard-code keys for mail, web push, or
third-party APIs. Use `config/settings/*` to separate local vs. production configs, and prefer feature flags/settings
constants over inline literals when adding new toggles.
