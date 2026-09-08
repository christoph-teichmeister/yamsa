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
Tailwind utilities (`flex`, `px-2`, `gap-2`, etc.) and HTMX attributes instead of custom CSS whenever
possible. Keep static JS modular inside `static/js/` and co-locate SCSS/CSS with the component it styles. **Edit
canonical static assets under `apps/static/…` (e.g., `apps/static/js/navigation.js`) and let hashed copies
in `static/`/`staticfiles/` be generated artifacts.**

Avoid module-level `__all__` exports; we prefer importers to rely on explicit names so tooling can track usage without
additional declarations. Never use relative imports inside the apps — prefer absolute imports anchored at the project
root (e.g., `from apps.transaction import models`).

## Design System & UI Concepts

- Tailwind CSS 4 is the design system, and [`design.md`](design.md) is its reference: the palette, the canonical
  class strings for every pattern, and the rules a page has to follow. Reach for a utility before custom CSS.
- Layouts should feel airy: a page section is `@container mx-auto flex w-full max-w-3xl flex-col gap-4`, its
  contents sit in a sheet or in cards, and emphasis comes from `shadow-card`.
- Primary CTAs are full-width or paired buttons with icons (`{% icon %}`) and consistent spacing (`gap-2`). Avoid duplicate
  actions; prefer a single, well-labeled button per task.
- Content blocks stack, and widen with a container query (`@lg:grid-cols-2`) rather than a viewport breakpoint, so a
  partial reads the space it was actually given.
- Keep typography calm: headings use `font-semibold`, supportive text is `text-sm text-ink-muted`; badge colours
  convey status through the `success-*`/`warning-*`/`danger-*` token pairs.
- When using HTMX, ensure loaders target `#body`, and actions that mimic navigation also manage scroll restoration (see
  `apps/static/js/navigation.js`).
- Wherever a user's name appears, their avatar comes from `shared_partials/_user_avatar.html` (classes `.avatar`,
  `.avatar-sm|-lg|-square|-pair` in `apps/static/customClasses.css`). It takes values, not a user, and falls back to the
  initial when `avatar_url` is empty. Read the picture through `User.avatar_url` — never `profile_picture.url` — because
  that property caches the storage existence check and narrows the Cloudinary URL to thumbnail size; `profile_picture_url`
  stays the full-size variant for the profile page.

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

## Offline: what the app promises without a connection

Three pieces, in `apps/core` and `apps/static/js/offline.js`:

**The service worker** (`core/pwa/serviceworker.js`, rendered by `ServiceWorkerView`) keeps two
caches. Assets go to `yamsa-static-<version>`, shared by everyone. Documents go to
`yamsa-pages-<version>-<scope>`, where the scope comes from `PwaScopeHeaderMiddleware` and names
the signed-in account. Only one page cache exists at a time — that is how the worker recognises
its own while offline, when it has no session to ask. Both are network-first: the cache is the
fallback, never the source.

**The page** reports its scope on every load and after every htmx swap, which is what makes a
sign-out drop the previous account's pages (a sign-out is an htmx request the worker never sees).
It also asks the worker to warm the room from `room:offline-manifest` — the dashboard tabs plus the
expense form. The worker does the fetching, because a `fetch()` the page makes is not a navigation
and would not be recognised as a document.

**The outbox** (`apps/static/js/outbox.js`, IndexedDB) holds an expense entered without a
connection. The page writes it, the worker replays it — a queue that only drains while a tab is
open is not a queue. The replayed body is the one the form would have posted, against the same
view, so there is no second write path to keep in step.

The cache names carry a version, and a deploy that leaves it unchanged keeps every browser on the
release before. It comes from the `RELEASE` setting, which Sentry is initialised from as well —
one name for both readers, so a third source cannot reach one and miss the other. `RELEASE` is
`SENTRY_RELEASE` where somebody configured one, otherwise `RENDER_GIT_COMMIT`, which Render sets
on every deploy of a git-backed service in both the build and the runtime environment. Where
neither exists — a working copy, another host — a hash of the asset manifests stands in for the
cache name. Nothing here needs a variable set by hand.

Things that will bite you here:

- **`Vary`.** Django answers these pages with `Vary: Cookie, Accept-Language`. A warmed page is
  fetched by the worker rather than by a navigation, so the two never agree on those headers.
  Every read of the page cache passes `ignoreVary: true`; what `Cookie` separates is the account,
  and the cache is already partitioned by exactly that.
- **The offline stand-in reports no scope.** It is precached without an account and then shown for
  any page that cannot be reached. Reporting a scope read as a sign-out, and one unreachable page
  emptied the whole cache.
- **Warming makes GETs repeat.** A request that only fills the cache carries
  `PREFETCH_HEADER_NAME`; anything that changes state once on a GET — the reminder heartbeat, the
  one-shot import hint — checks for it and stands down.
- **`client_request_id` is minted per submission, not per form.** The form is served from the
  cache, so every expense entered offline starts from the same copy; the outbox overwrites the
  rendered id with its own. `ParentTransaction.client_request_id` is unique, and
  `TransactionCreateView` answers a replay with the first submission's outcome and no second event.
- **Background Sync does not exist on iOS.** The queue drains there when the app is opened again,
  not before. The pending strip says so where `SyncManager` is missing, and nothing in the UI words
  a queued expense as sent.
