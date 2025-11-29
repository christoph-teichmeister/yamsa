# Issue 297 - Migrate to pytest

## Title
Migrate to pytest

## Body
### User Story
Als Entwickler in diesem Repository möchte ich die Testautomatisierung von Django`s TestRunner auf `pytest` umstellen, damit ich von dessen moderneren Fixtures, besserer Modularität und Community-Ökosystem profitieren kann.

### Context
Derzeit laufen alle Tests über den eingebauten Django-Test-Runner, was den Einsatz etablierter `pytest`-Features verhindert. Viele Apps nutzen bereits eigene Setup-Logiken und Ressourcen wie Factories, die von `pytest` besser orchestriert werden könnten. Es fehlt eine gemeinsame `conftest.py`-Basisschicht und strukturierte Konventionen für wiederverwendbare Fixtures.

### Business Value
- Schnellere und stabilere Tests durch `pytest`-Optimierungen, z.B. parametrisiertes Testen und einfacheres Mocking.
- Einheitliche Testkonventionen reduzieren Wartungskosten und erleichtern Onboarding neuer Entwickler.
- Bessere Integrationsmöglichkeiten mit Tools wie `pytest-cov`/`pytest-django` für zukünftige CI-Visibility und Coverage.

### Acceptance Criteria
- [ ] Alle Django-Tests laufen grundsätzlich via `pytest` und nicht mehr über `manage.py test`.
- [ ] Es existiert eine gemeinsame `conftest.py` im Projekt-Root (oder `apps/`-Scope), die zentrale Fixtures (Django settings, DB, Factory-Bootstrap) bereitstellt.
- [ ] Jede App hat mindestens einen Beispiel-Test, der die neuen Fixture-Konventionen nutzt (z.B. Factory, Client).
- [ ] Die Umstellung ist dokumentiert (README/CONTRIBUTING oder docs/), inklusive Befehle zum lokalen Ausführen.
- [ ] Linting/Check-Tools bleiben kompatibel (z.B. `uv run ruff check` und `uv run coverage run ...` müssen weiterhin funktionieren oder werden angepasst).

## Labels
- _None_

## Comments
- _None_

## Technical Tasks
- **Backend**
  - Evaluate current Django tests (`apps/*/tests/`) and migrate them to `pytest`, ensuring at least one app acts as a proof-of-concept.
  - Introduce `apps/conftest.py` (or root `conftest.py`) with shared fixtures for Django settings, test client, and commonly used models/factories.
  - Create or update Factory setup (e.g., using `factory_boy`) to be importable from fixtures; place them under `apps/*/tests/factories.py` or similar.
  - Adjust existing Django `TestCase`s to `pytest` functions/classes as needed, using `pytest.mark.django_db` and dependencies like `pytest-django`.
  - Ensure migrations or DB setup steps are compatible with `pytest` (e.g., via `django_db_reset_sequences=True` where necessary).
  - Add tests demonstrating fixture usage and register commands in documentation for running `uv run pytest`.
- **Frontend**
  - (If template-specific tests exist) Update or create HTMX/Template-related tests under `apps/*/tests/` to use `pytest` fixtures/client.
  - Document any frontend testing practices (e.g., leveraging `pytest` client) in `docs/` or per-app README.
- **Other**
  - Update CI scripts (`pyproject.toml`, `docs/` or GitHub workflows) to call `uv run pytest` instead of `python manage.py test`.
  - Add any necessary dev dependencies (`pytest`, `pytest-django`, `factory-boy`, `pytest-factoryboy`) to Poetry/pyproject.
  - Provide migration path for running coverage via `uv run coverage run -m pytest` and ensure `coverage report` still works.

## Open Questions / Risks
- Müssen bestehende `manage.py test`-Aufrufe in Dokumentation/CI vollständig entfernt oder kann es einen Übergangszeitraum geben? -> Vollständig entfernt
- Gibt es Tests, die stark von Django`s TestRunner-Features abhängen (z.B. `SimpleTestCase`, Custom Test Suites), die Sonderbehandlung benötigen? -> Nein.
- Welche Apps/Module definieren aktuell ihre eigenen Test-Setups, und wie sollen diese sauber in die neue `conftest.py` integriert werden? -> Keine Ahnung
