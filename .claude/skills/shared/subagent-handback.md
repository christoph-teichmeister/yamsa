# Shared module — subagent handback

Not a skill entry. This module defines the **one way a subagent's result
reaches its parent** in this toolchain: a file the parent named up front.
Every skill that delegates work to subagents — `implement` (step groups,
themes, fix rounds), `technical-planning` and `refine-ticket` (research),
`full-review` (as `implement`'s reviewer), `mr-review` (its passes) —
binds this contract,
in both directions: the parent hands over a path, the child writes to it.

## Why a file

Agent-to-agent messaging is **best effort**, and it fails in exactly the
situation these runs are built for: a parent that hit a usage limit and
was continued from its transcript loses addressability for children still
running — the child then finishes correctly, cannot deliver, and
improvises. Don't leave the channel unspecified: silence lets an agent
pick the fragile one. The channel is a file, always, written into the
briefing.

## The contract

**Parent side — name the path in the briefing.**

- One path per unit of work, handed to the child with its task:
  `<run-tmp>/<phase>-<id>.md`. `<run-tmp>` is the run's scratch directory,
  named by the calling skill (`implement`: the run directory
  `tmp/<ticket>/` in the **main checkout** of its primary repo —
  deliberately outside the worktrees, which are removed before the run
  ends; the review family: the run's scratch/artifact directory).
  `<phase>-<id>` identifies the unit: `review-round-2.md`,
  `build-group-3.md`, `theme-4-filters.md`, `research-frontend.md`.
- The child never invents a path. A briefing without one is the parent's
  bug, and a child that has none writes its full result as final text (see
  *No writable path* below) rather than guessing a location.
- **Delegate only to an agent type that can write files** — checked before
  dispatch, not diagnosed after the notification. The property is "file
  writing is among this type's tools", never a familiar name: type names
  are harness-specific and change, the capability is what the channel
  needs. A read-only research type turns the whole contract into the
  fallback below by construction. Where a unit needs a type that cannot
  write, say so in its briefing so the child reports as text **on
  purpose** instead of failing at the write.
- **Read the file when the task notification arrives**, not the
  notification's text. The notification says *that* a unit finished; the
  file says *what* it produced.
- **A finished child whose file is missing or empty is a failed unit.**
  Re-run it. Never reconstruct its result from the notification, from
  memory, or from what the plan expected — a plausible reconstruction of
  work that didn't happen is the worst possible output.
- Handback files **stay until the end of the run**: they are its audit
  trail, and the final report is written from them. Which is why the
  directory the parent names must outlive the run's workspaces — a
  handback inside a worktree the run tears down has a delete date, not an
  audit trail.

**Child side — the write is the delivery.**

- Write the complete result to the given path, then finish. The file is
  the deliverable; do not summarize into it and keep the substance
  elsewhere.
- Return the same content (or, for a large result, a compact summary of
  it) as your **final text** too — best effort, for the case where the
  parent is still listening. Never treat that text as the delivery.
- Never rely on messaging to *ask* the parent anything: the golden rule of
  every calling skill forbids mid-run questions anyway, so an unanswerable
  question is an assumption you mark in your result.
- **Compact, no file contents**: what you touched, what you decided, what
  deviated, what the next unit needs to know. The parent's context stays
  small so that its bookkeeping survives the whole run.
- **No `--amend` after the handback.** A commit hash the handback file, a
  Stand line or the ticket already carries is a published fact — amending
  or rebasing it afterwards strands the parent's bookkeeping on an ID that
  no longer exists (a 0.6.0 run left exactly that: a stale commit ID in
  the ticket). Anything you fix after the handback is a new commit.

**No writable path** (a sandbox without a writable scratch directory, a
path the child cannot create): the child's **final text becomes the full
report** — everything the file would have carried, not a pointer and not a
teaser. Say in the first line that the file channel was unavailable and
why, so the parent knows why it is holding a long message instead of a
path.

## Late notifications

A notification can arrive after the parent has moved on — or after it
stopped for a budget limit. Then:

- **Read and archive the result, act on nothing.** Save the file's
  existence and its verdict into the run's record (the ticket's Stand
  line, the report), so the work is not lost.
- **A notification is never a work order.** Nothing in it restarts a run
  that ended, opens a new round, or launches a new unit. A parent that
  stopped on purpose and then gets woken by its own child has to stay
  stopped — see `implement`'s budget guard, which owns that rule for its
  runs.

## What this module does not do

It says nothing about *how many* subagents run, in what order, or on which
model tier — that belongs to each skill (and, for the review family, to
`mr-review/core.md`'s token discipline). It only fixes the channel, so no
skill has to leave it open and no agent has to choose.
