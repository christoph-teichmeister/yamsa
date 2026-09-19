# Testing

Place tests beside their apps under `apps/*/tests/` using `test_<unit>.py` naming and write them with PyTest as the
preferred runner. Structure each PyTest module as a class that groups its test methods (mirroring Django's test runner
best practices) instead of scattering standalone functions. When you need models, instances, or complex recipes, define
fixtures in `conftest.py` and rely on factories rather than ad-hoc object creation — put every factory implementation
in `factories.py` (app-level if specific to one app, or a shared `conftest.py`/`factories.py` for cross-app reuse).
Aim for coverage parity with existing badges (>85%); add regression tests when touching business-critical flows such as
settlement math or transaction rendering.

## Logging in for manual or Playwright-driven testing

Auth is a custom `account.User` model with email-based login (django-axes reads `email` as the
username field) — not Django's default username/password, not allauth.

Seed the local database once per session against a running server:

```
uv run python manage.py restore_test_data
```

This flushes the DB and creates fixed-credential accounts (all password `Admin123$`):

| Role             | Email                            |
|------------------|-----------------------------------|
| Superuser        | `admin@yamsa.local`               |
| Registered user  | `registered_user_1@yamsa.local` … `registered_user_5@yamsa.local` |

Guest users (`guest_1`…`guest_5`) are also seeded but have no usable password by design
(`User.clean()`) — they can only authenticate through a room-invite link
(`AuthenticateGuestUserView`), never through the login form.

Login form: `/account/login/`, fields `#id_email` / `#id_password`, submit
`#login-submit-button` (see `apps/account/forms/login_form.py` and
`account/partials/_password_field.html`, whose `id_password` id is kept stable for exactly
this reason). A failed login renders `#login-error`.

For the copy-paste `playwright-cli` flow, see
`.claude/skills/playwright-cli/references/yamsa-login.md`.

## Richer test data for design/UX QA

`restore_test_data` alone leaves every room empty (it creates no transactions at all). For design
work that needs real content density - long lists, multiple currencies, settled and unsettled
debts, a genuinely empty room - run this on top of it:

```
uv run python manage.py restore_test_data
uv run python manage.py create_intensive_test_data
```

`create_intensive_test_data` reuses the same fixed-credential users (`get_or_create`, so it layers
cleanly rather than duplicating them) and adds 7 rooms: 6 populated with 25 transaction scenarios
each across 4 currencies (EUR/GBP/USD/CHF) and a mix of settled/unsettled debts, plus one
single-member room ("Nobody's Moved In Yet") that the transaction/debt creation steps skip by
construction - a curated empty-state fixture, not an accidental one.

## Testing the service worker

Service worker behaviour is only real in a browser, so it lives in `e2e/` rather than in a JS unit
suite. Two things about the harness:

- **`page.context.set_offline()` does not reach the worker.** It only covers requests the page
  itself makes; a `fetch()` the worker issues is still answered, and the cache would never be the
  thing under test. `e2e/tests/core/test_offline.py` routes every request to `route.abort()` as
  well, and keeps `set_offline` for what `navigator.onLine` reads.
- **`page.wait_for_function()` cannot await.** It polls its predicate synchronously and reads a
  returned Promise as truthy, so a condition that has to read cache storage or IndexedDB always
  passes on the first tick. Poll from Python with `page.evaluate()` instead — `_wait_until()` in
  that module does it.

