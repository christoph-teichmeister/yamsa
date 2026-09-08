# Testing

Place tests beside their apps under `apps/*/tests/` using `test_<unit>.py` naming and write them with PyTest as the
preferred runner. Structure each PyTest module as a class that groups its test methods (mirroring Django's test runner
best practices) instead of scattering standalone functions. When you need models, instances, or complex recipes, define
fixtures in `conftest.py` and rely on factories rather than ad-hoc object creation — put every factory implementation
in `factories.py` (app-level if specific to one app, or a shared `conftest.py`/`factories.py` for cross-app reuse).
Aim for coverage parity with existing badges (>85%); add regression tests when touching business-critical flows such as
settlement math or transaction rendering.

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

