# Architecture

## Project Structure

The project is a Django monolith rooted at `manage.py`. Domain-specific logic lives inside `apps/`, e.g.
`apps/transaction`, `apps/room`, and `apps/account`; each app contains its own `models`, `views`, `templates`, and
`tests`. Shared templates and assets belong in `apps/templates` and `static/`, while compiled artefacts land in
`staticfiles/`. Developer tooling scripts sit in `scripts/` and container assets in `Dockerfile`, `docker-compose.yml`,
and `entrypoint.sh`. Documentation, including AI prompt history, lives in `docs/`.

## Coding Style & Naming Conventions

Follow Python's 4-space indentation and keep modules typed where practical. Use `snake_case` for functions, `PascalCase`
for classes, and `SCREAMING_SNAKE_CASE` for settings. Run `uv run ruff check --fix .` before committing; it handles
import order, linting, and selected auto-fixes. Templates must pass `uv run djlint apps --reformat`; lean on
Bootstrap 5 utility classes (`d-flex`, `px-2`, `gap-2`, etc.) and HTMX attributes instead of custom CSS whenever
possible. Keep static JS modular inside `static/js/` and co-locate SCSS/CSS with the component it styles. **Edit
canonical static assets under `apps/static/…` (e.g., `apps/static/js/navigation.js`) and let hashed copies
in `static/`/`staticfiles/` be generated artifacts.**

Avoid module-level `__all__` exports; we prefer importers to rely on explicit names so tooling can track usage without
additional declarations. Never use relative imports inside the apps — prefer absolute imports anchored at the project
root (e.g., `from apps.transaction import models`).

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

## Forms vs Views — Separation of Concerns

`ModelForm.save()` must only validate and persist data to the database. It must not:

- Own a `transaction.atomic()` boundary — that belongs in the view's `form_valid()`
- Call `handle_message()` or trigger any other side effects

Side effects (event dispatch, notifications, debt recalculation via `handle_message`) belong in the view's
`form_valid()`, called **after** the `transaction.atomic()` block exits. This ensures downstream handlers (e.g. webpush
HTTP calls) never hold the DB connection open inside an atomic block, which would cause consecutive requests to block or
fail (see #333).

```python
# ✅ Correct pattern in form_valid()
def form_valid(self, form):
    with transaction.atomic():
        self.object = form.save()
    handle_message(SomeEvent(context_data={...}))  # after atomic, connection is free
    return super().form_valid(form)
```
