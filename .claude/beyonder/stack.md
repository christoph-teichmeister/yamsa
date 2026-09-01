# Review checks: Django + Bootstrap/HTMX + PostgreSQL

## Backend pass (Django)
- N+1 queries: loops over querysets/serializers/template context without `select_related`/`prefetch_related`
- Missing or irreversible migrations; migrations not reviewed alongside the model change that produced them
- `ModelForm.save()` holding side effects or a `transaction.atomic()` boundary — per AGENTS.md/docs/ai/architecture.md, that belongs in the view's `form_valid()`, called after the atomic block exits (see #333)
- `.save()` without `update_fields` on hot paths
- Relative imports inside `apps/` (project convention: absolute imports anchored at project root)
- Module-level `__all__` exports (project convention: avoid)

## Frontend pass (Bootstrap 5 / HTMX / D3)
- HTMX loaders not targeting `#body`; actions that mimic navigation not managing scroll restoration (see `apps/static/js/navigation.js`)
- Editing hashed/generated copies under `static/`/`staticfiles/` instead of canonical sources under `apps/static/…`
- Custom CSS reaching past Bootstrap 5 utility classes without justification
- Duplicate primary CTAs on one screen (project convention: single well-labeled action per task)

## Validation notes
- Templates must pass `uv run djlint apps --check` (CI) / `--reformat` (local)
- `uv run ruff check --output-format=github .` is the CI lint gate; `--fix` locally
- `uv run python scripts/check_one_class_per_file.py --fail-on-multiple` enforces one class per file
- Test DB defaults to SQLite (`DJANGO_DATABASE_URL` unset) — a migration or DB-specific behavior verified only against SQLite may still break on the docker-compose Postgres 18 service
