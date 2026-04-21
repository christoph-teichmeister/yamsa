# Testing

Place tests beside their apps under `apps/*/tests/` using `test_<unit>.py` naming and write them with PyTest as the
preferred runner. Structure each PyTest module as a class that groups its test methods (mirroring Django's test runner
best practices) instead of scattering standalone functions. When you need models, instances, or complex recipes, define
fixtures in `conftest.py` and rely on factories rather than ad-hoc object creation — put every factory implementation
in `factories.py` (app-level if specific to one app, or a shared `conftest.py`/`factories.py` for cross-app reuse).
Aim for coverage parity with existing badges (>85%); add regression tests when touching business-critical flows such as
settlement math or transaction rendering.
