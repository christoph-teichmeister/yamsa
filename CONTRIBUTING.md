# Contributing to yamsa

This project pins its dependencies via `pyproject.toml` and `uv.lock`. Workflows revolve around `uv`, so follow the
steps below before submitting changes:

## Getting started

- Install `uv` globally (e.g. `python -m pip install --user uv`) so you can run `uv sync` and `uv run`.
- Bootstrap the workspace with `uv sync --all-extras --no-install-project`. That creates the `.venv` directory and
  installs both production and development dependencies.
- Use `uv run python manage.py migrate` and `uv run python manage.py runserver 0.0.0.0:8000` when iterating locally.

## Testing and linting

- Unit tests: `uv run python manage.py test apps`.
- Coverage: `uv run coverage run manage.py test && uv run coverage report`.
- Formatting: run `uv run ruff check --fix .` followed by `uv run djlint apps --reformat`.

## Lockfile updates

- After adding, removing, or updating dependencies in `pyproject.toml`, run `uv lock` and commit the generated
  `uv.lock`.
- If you need a `requirements.txt` for a deployment or Docker image, run
  `uv export --locked --format=requirements.txt --no-dev --output-file /tmp/requirements.txt` and feed that file into
  `pip install -r`.
- Keep `.venv/` ignored (`.gitignore` already excludes it) so the lockfile remains the sole source of truth.

## Troubleshooting

- If `uv sync` reports a lock mismatch, re-run `uv lock`, followed by `uv sync --no-install-project --locked` to ensure
  the lockfile and environment agree.
- Use `uv run python manage.py shell` for inspect data, and rerun `uv run python manage.py migrate` after schema
  changes.

Remember to follow the conventional commit style documented in the repository guidelines when preparing your commits.
