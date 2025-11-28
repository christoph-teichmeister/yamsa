# yamsa

Yet another money split app

---

![code coverage](https://camo.githubusercontent.com/b472dc5f8ea152d257c7daebef2fcbf2a5f6122a980eba2b0f8290ee04b786d4/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f436f6465253230436f7665726167652d38362532352d737563636573733f7374796c653d666c6174)

---

#### Some Links for quick access

* [htmx docs](https://htmx.org/docs/)
* [bootstrap icons](https://icons.getbootstrap.com)
* [bootstrap docs](https://getbootstrap.com/docs/5.3/getting-started/introduction/)

#### PWA-relevant Links

- [pwa install prompt](https://medium.com/@hadxit/how-do-you-develop-a-pwa-install-prompt-63c24fa2d0f2)
- [URL Protocol Handler for PWAs](https://developer.chrome.com/docs/web-platform/best-practices/url-protocol-handler)
- [PWA => App Builder](https://www.pwabuilder.com/reportcard?site=https://yamsa.onrender.com)

## Development

The Django stack is managed through `uv` with a `.venv` stored beside the project. Before working on the app:

1. Install `uv` if you don’t already have it (e.g. `python -m pip install --user uv`).
2. Run `uv sync --all-extras --no-install-project` to populate `.venv` with the pinned dependencies.
3. Use `uv run python manage.py migrate` to align the database schema and
   `uv run python manage.py runserver 0.0.0.0:8002` to start the local server.

## Testing & Quality

- `uv run python manage.py test apps` runs the Django app suite inside `uv`’s environment.
- `uv run coverage run manage.py test && uv run coverage report` generates coverage reports (see `pyproject.toml` for
  configuration).
- Run `uv run ruff check --fix .` and `uv run djlint apps --reformat` to keep formatting consistent.

## Dependency & Lockfile Workflow

- Dependencies live in `pyproject.toml` and lock metadata is captured in `uv.lock`. Always run `uv lock` after adding or
  updating requirements and commit the lockfile together with the code changes.
- When you need a `requirements.txt` (e.g., Docker image builds, Render deploys), run
  `uv export --locked --format=requirements.txt --no-dev --output-file /tmp/requirements.txt` and share that file with
  the installation step.
- If a dependency mismatch is reported (`uv sync` urges `uv.lock` changes), rerun `uv lock`, verify
  `uv sync --no-install-project --locked` succeeds, and commit the updated `uv.lock`.
- Run `uv lock --check` to verify that the lockfile is up to date and `uv lock --upgrade` to upgrade it.
