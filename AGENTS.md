# AGENTS.md — project knowledge

<!-- Written by beyonder-setup. This is the project's ONE knowledge file
(E-0030): project knowledge and the baseline sections below live here,
and only here. CLAUDE.md is a pure @AGENTS.md entry point and never
gains content of its own. Keep this file small: rules only earn a line
if they change an agent's behavior in THIS project. -->

## Hard rules

- `ModelForm.save()` (any app under `apps/`) must only validate and persist data. It must not own a `transaction.atomic()` boundary or call `handle_message()`/trigger other side effects — both belong in the view's `form_valid()`, called after the atomic block exits. Violating this held a DB connection open inside an atomic block and made consecutive requests block or fail (see #333, docs/ai/architecture.md § Forms vs Views).

<!-- TBD — collect with the team; do not invent. -->

## Temporary files

- Create temporary files (scratch scripts, intermediate results, test
  data, one-off outputs) in `tmp/` inside the project — never in system
  temp directories. Create it with `mkdir -p tmp` if missing; full
  read/write/delete inside `tmp/` without asking.

## Comment policy

- Comments name constraints, invariants and whys the code cannot show;
  public API gets doc comments; no narrative comments (what the next line
  does, where code came from, why a change is correct).
- The rule cuts both ways: a missing constraint comment is as much a
  finding as narrative noise.

## Language

- Code, code comments, commit messages: English.
- Tickets and PR descriptions: German (team decision 2026-09-01).

<!-- TBD (collect with the team — do not invent): none currently — branch
naming, commit format/granularity/push-policy/squash-policy and PR
description format are settled in .claude/beyonder/workflow.md and
docs/ai/workflow.md § Commit & Pull Request Guidelines.
beyonder-setup step ③ fills sections here only from real team answers. -->

## Project knowledge

AI-specific documentation lives in [`docs/ai/`](docs/ai/):

- [`architecture.md`](docs/ai/architecture.md) — project structure, coding conventions, design system, and architectural patterns
- [`testing.md`](docs/ai/testing.md) — testing guidelines and conventions
- [`workflow.md`](docs/ai/workflow.md) — build commands, commit/PR guidelines, and PR review workflow
