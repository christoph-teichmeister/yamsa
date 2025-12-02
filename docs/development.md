# Development Guide

## Prerequisites

- Python 3.11 (the Docker images and production deployments target `python:3.11`).
- `uv` as the dependency manager (`python -m pip install --user uv` or via your OS package manager).

## Datenbank-Setup

- Die lokale Docker-Umgebung nutzt `postgres:18-alpine` (siehe `docker-compose.yml`), damit Development und CI die
  gleiche Major-Version verwenden.
- Starte die Datenbank (`docker compose up database` oder ähnliche Scripts aus `scripts/`) bevor du
  `uv run python manage.py migrate` ausführst; alle Befehle laufen gegen Postgres 18.
- Import-Anleitungen (z. B. in `apps/docs/notes.md`) setzen auf dieselben Zugangsdaten und Ports wie in
  `docker-compose`, sodass Dumps direkt in die neue Version eingespielt werden können.

## Bootstrapping dependencies

1. Run `uv sync --all-extras --no-install-project` to install the locked dependency set into the local `.venv`.
2. Keep `.venv` ignored; rely on `uv.lock` for reproducibility.
3. When you change dependencies, re-run `uv lock` and commit both `pyproject.toml` and `uv.lock`.
4. If you need a requirements intermediary for Docker or Render,
   `uv export --locked --format=requirements.txt --no-dev --output-file /tmp/requirements.txt` produces a pip-friendly
   list.

## Running the Django app

- `uv run python manage.py migrate` applies migrations.
- `uv run python manage.py runserver 0.0.0.0:8002` starts the development server in the `uv` environment.
- `uv run python manage.py shell` launches a Django shell.

-## Testing and linting
- `uv run pytest` exercises the backend test suite using the shared fixtures defined in `conftest.py` and
  `apps/*/tests/factories.py`.
- `uv run coverage run -m pytest && uv run coverage report` generates coverage data as configured in
  `pyproject.toml`.
- Run `uv run ruff check --fix .` followed by `uv run djlint apps --reformat`.

## Session management

- Logging in stores the target TTL under `apps.account.constants.SESSION_TTL_SESSION_KEY` and the new
  `apps.core.middleware.session_keep_alive_middleware.SessionKeepAliveMiddleware` re-applies it on every meaningful
  authenticated request, so the cookie keeps sliding as you stay active.
- Remember-me continues to use `DJANGO_REMEMBER_ME_SESSION_AGE` while the standard path runs against
  `SESSION_COOKIE_AGE`, but both paths now refresh automatically and clean up the metadata on logout.
- Once the configured window elapses without requests, Django still expires the session and the next protected
  view routes to `account:login`, proving the sliding window only works while activity is maintained.

## Troubleshooting

- Lockfile mismatches? Run `uv lock`, then `uv sync --no-install-project --locked` to ensure the environment matches the
  lock.
- `uv sync` tries to install the current project by default; supply `--no-install-project` when you only want the
  dependencies.
- Docker builds call `uv export --locked --format=requirements.txt` before pip installing, so keep `uv.lock` up to date
  for CI parity.
