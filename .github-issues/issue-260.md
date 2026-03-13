# Issue #260: Determine whether runner still needs event/command autodiscovery

## Issue
`apps/core/event_loop/runner.py` still carries a commented-out block that used to call `message_registry.autodiscover()` even though the TODO comments claim auto-registration moved to `apps.core.apps.CoreConfig.ready`. The issue is to confirm the current bootstrapping location, remove any redundant code from the runner, document where the registry is populated, and insure future changes do not break this flow.

## Technical Tasks
- [ ] Confirm that `message_registry.autodiscover()` runs during Django startup (see `apps.core.apps.CoreConfig.ready`) so the runner does not need to import or register the registry itself.
- [ ] Remove the commented-out autodiscovery block from `apps/core/event_loop/runner.py` and add a docstring or comment stating that registration happens on Django startup.
- [ ] Add a regression test covering the event loop runner to ensure it still dispatches commands/events properly once the registry has been populated.

## Notes / Open Questions
- None.
