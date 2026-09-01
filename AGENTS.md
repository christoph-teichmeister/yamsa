# AGENTS.md — project knowledge

<!-- Written by beyonder-setup. This is the project's ONE knowledge file
(E-0030): project knowledge and the baseline sections below live here,
and only here. CLAUDE.md is a pure @AGENTS.md entry point and never
gains content of its own. Keep this file small: rules only earn a line
if they change an agent's behavior in THIS project. -->

## Hard rules

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

<!-- TBD (collect with the team — do not invent):
- Host conventions: branch naming, MR/PR description format
- Commit conventions: message format, granularity, push + draft-MR,
  squash policy
- Language rules: German or English in tickets/MRs/code comments
beyonder-setup step ③ fills these sections only from real team answers. -->

## Project knowledge

AI-specific documentation lives in [`docs/ai/`](docs/ai/):

- [`architecture.md`](docs/ai/architecture.md) — project structure, coding conventions, design system, and architectural patterns
- [`testing.md`](docs/ai/testing.md) — testing guidelines and conventions
- [`workflow.md`](docs/ai/workflow.md) — build commands, commit/PR guidelines, and PR review workflow
