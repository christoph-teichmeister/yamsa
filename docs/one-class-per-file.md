# One Class per File

This repository now follows a strict **one class per module** convention for the core domain code because
it makes navigation, refactoring, and tooling more predictable. Every exported class therefore lives in a
dedicated file, and any helpers or mixins needed by that class should be colocated or split into their own
modules as appropriate.

## When multiple classes were previously grouped together

- Move each class into `apps/<app>/<role>/<class>.py` (e.g., `apps/transaction/models/transaction.py`).
- Create an `__init__.py` alongside the fragmented modules if you still need a package-level namespace; re-export
  the individual classes via `from .transaction import Transaction` so callers keep writing
  `from apps.transaction.models import Transaction`.
- Keep module-level decorators (like `@admin.register`, `@dataclass`, or `@shared_task`) on the same file as the class
  they decorate.

## Verification

Use the audit script before committing or in CI to detect regressions:

```
python scripts/check_one_class_per_file.py --fail-on-multiple
```

Any violations will be listed with the number of classes discovered and the offending module path. If you need a
full report (for example when working on a refactor that touches many files), add `--report tmp/multi-class.json`.

## When this rule might evolve

We still allow module-level helpers, factories, and constants in the same file so long as they do not declare
additional classes. If a small helper class is only used by one other class, evaluate whether it can be folded as
a nested class or rewritten as a function before creating its own module.
