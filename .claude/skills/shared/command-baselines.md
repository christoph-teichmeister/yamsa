# Shared module — command baselines

Not a skill entry. This module defines how a configured command becomes a
**trustworthy gate**: measure it once against the base state (the setup
branch — base plus the setup's own commit, see *Measure*), record what it
reports there, and derive whether a review may adjudicate it at all.

`beyonder-setup` (step ④) runs the measurement and writes the result;
`mr-review` reads it and honors the verdict. Change the rules here and
every caller follows.

## Why this exists

A command is not present-or-absent, it is present-and-clean or
present-and-already-failing. Almost no mature repo is clean on every tool
it has configured. Written in as a gate, an already-failing tool reports
"validation failed" for **every review, forever** — noise that tells the
reviewer nothing and trains them to ignore the section.

Worse, if code that is **already merged** fails a tool, the team does not
enforce that tool in practice. A review that flags it is adjudicating a
rule the team never adopted.

## Measure

Per command slot in `workflow.md` (validate/build, tests, lint/format,
migrations check), once, at setup time:

1. Note the branch the repo is checked out on, then check out the
   **setup branch** (`beyonder-setup/<YYYY-MM-DD>`, created from the tip
   of the base branch per `workflow.md`; `beyonder-setup` ④ creates it
   and commits the setup's own files there first) with a clean working
   tree. Never measure on the base branch itself: a branch guard
   (`no-commit-to-branch`) fails exactly there, and the `dirty:1` it
   produces is an artefact of the measuring place, not of the repo. The
   baseline therefore describes **base + setup changes** — the state the
   team will merge — and proves on the side that the setup introduces no
   violations. A dirty tree still invalidates the measurement — stash or
   abort, never measure over local changes. When done, **return the
   repo to the branch you found it on** — leave every repo the way you
   found it.
2. Run the command once. Record exit code and a **count** of what it
   reports (violations, failing files, errors), not the full output.
3. Note the wall-clock duration. A slot over ~2 minutes gets a `slow:`
   note so callers can decide to scope it.
4. If the command cannot be run non-destructively, do not run it — see
   *Stacks with no non-destructive check* below.

Measure with the project's own invocation (the one going into
`workflow.md`), not a variant you consider cleaner.

Two rules about *running* a measurement, both learned the expensive way:

- **Measurements are strictly serial — never two at once.** They share
  the databases, ports and caches that the parallel-run recipe
  parameterises for *runs*; a measurement has no slot of its own, so two
  concurrent ones collide exactly the way the generated isolation block
  warns about, and both numbers are contaminated.
- **An empty output file is not proof of a dead run.** Test runners
  buffer fully when piped — a background run can be minutes in with a
  zero-byte log. Before declaring a run dead, check that the process is
  gone **and** a sensible timeout has passed; never start a replacement
  run beside one that may still be alive.

### Baselines are tree-dependent

A command's result depends on **which kind of tree** it runs in, not
only on the branch: a fresh worktree misses the main tree's gitignored
config (`.env`, `.env.*`), and path-keyed environments (a Poetry venv
outside the repo, a per-directory `node_modules`) don't follow the code
into a new path. The same suite can be `clean` in the main tree and
fail app-wide in a worktree off the same commit — an environment
difference, not a regression.

Every baseline therefore carries a tree qualifier, `@maintree` or
`@worktree`; a baseline without one reads as `@maintree`. For the
**gate command** (the slot the review loop leans on, typically tests),
measure twice: once in the main tree, once in a throwaway worktree
(bootstrapped per `implement`'s worktree-needs checklist: gitignored
config in, dependencies installed for the new path), and record both
numbers. A mismatch between the two is a **finding about what a
worktree needs** — inventory the difference into the `## Isolation`
block instead of writing down the worse number.

Consumers honor the qualifier: a run in a worktree gates against the
`@worktree` baseline when one exists; a baseline measured only in the
other kind of tree is context, never a gate.

## Verdict

| Verdict | Meaning | How a review may use it |
|---|---|---|
| `clean` | exit 0, nothing reported | **Gate.** Failure is caused by the diff; report as a blocking finding. |
| `dirty:N` | N pre-existing findings in the measured base state (base + setup changes) | **Advisory only.** Report solely what the diff *introduces*; never the pre-existing N. |
| `unavailable` | not runnable non-destructively, or missing on this machine | Not a gate. Record why; use a heuristic if one exists. |
| `-` | deliberately disabled | Not run, not reported. |

`dirty:N` is not a defect to fix during setup. It is a fact about the
repo, and it belongs in the setup report as a **team decision to raise**:
"`black` reports 61 of 349 files on `develop` — is it meant to be
enforced? Until the team decides, reviews treat it as advisory."

## Recording it

In `.claude/beyonder/workflow.md`, each command carries its measurement as
a sub-attribute — `baseline:` alongside the existing `when:` / `targeted:`:

```markdown
- Lint/format: `poetry run flake8`
  - baseline: dirty:37 @ beyonder-setup/2026-08-09@a1b2c3d @maintree, 2026-08-09
  - scope: changed-files
- Tests: `poetry run pytest`
  - baseline: clean @ beyonder-setup/2026-08-09@a1b2c3d @maintree, 2026-08-09
  - baseline: clean @ beyonder-setup/2026-08-09@a1b2c3d @worktree, 2026-08-09
- Migrations check: -
  - baseline: unavailable — aerich has no dry-run mode
  - heuristic: `app/models/**` touched with no new `migrations/models/*`
```

The gate command carries both tree qualifiers (see *Baselines are
tree-dependent*); the other slots need only the tree they were measured
in, and no qualifier reads as `@maintree`.

The measured commit rides in the location, `@ <branch>@<short-hash>`: a
baseline is a claim about one commit, and the hash keeps the claim
attributable after the setup branch merges or moves. Baselines in the
older form (`@ develop`, branch + date, no hash) stay readable — the
date still drives staleness; only new measurements carry the hash.

The date matters: a baseline ages. A measurement older than the team's
tolerance (default: 90 days) is stale — `mr-review` preflight says so and
recommends re-running setup, but never blocks on it.

## Scoping an advisory command to the diff

For `dirty:N` slots, run the tool over the files the MR touches, not the
repo:

```bash
git diff --name-only --diff-filter=ACM origin/<base>...HEAD -- '<glob>' \
  | xargs -r <tool>
```

Notes that matter in practice:

- `--diff-filter=ACM` drops deletions, which would otherwise hand the tool
  paths that no longer exist.
- `xargs -r` (GNU) / `xargs` with a guard on BSD: without it an empty file
  list runs the tool over the whole repo, which is exactly the failure
  mode this recipe exists to avoid.
- Three-dot `origin/<base>...HEAD` gives the changes *on the branch*, not
  the difference to a moved base.
- Even scoped, a pre-existing violation in a touched file is not the
  diff's fault. Compare against the base-branch result for the same file
  set, or report only findings on **added/changed lines**.

## Stacks with no non-destructive check

Some tools have no dry-run. `aerich migrate` always writes a migration
file, so there is no way to *ask* whether migrations are missing. This is
not a gap in the setup — it is a property of the stack.

When a slot has no non-destructive check: set it to `-`, record
`baseline: unavailable` with the reason, and add a **diff heuristic** if
one exists (models touched, no migration added). Do not invent a
destructive invocation to fill the slot, and do not leave the slot silently
empty — `-` plus a reason is the answer.

## Rule for reviewers

**If merged code fails a tool, that tool is not enforced — a review must
not adjudicate it.** Surface it once as a team decision; do not re-raise
it per MR.
