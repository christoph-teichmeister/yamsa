---
name: walkthrough
description: >-
  Documents a feature with screenshots as it currently is: walks the flows the
  change touches in the running app and files the result where you point it —
  local report by default, a comment on the ticket, or a note on the MR/PR.
  Documents only, never reviews; the first problem aborts the run. Use when a
  feature should be shown or demoed, e.g. "/walkthrough" for the current
  branch.
argument-hint: <ticket id, branch, or MR/PR — defaults to the current branch> [--to local|ticket|mr]
hosts: any
tickets: any
---

# Walkthrough

You are producing a screenshot walkthrough of a feature — **not a
review**: no findings, no verdicts, no validation runs. The walkthrough
itself is the deliverable.

Your advantage: the people who decide whether the feature is done — the
PO, a stakeholder, the reviewer who won't pull the branch — see what was
built without running it.

## Prerequisites — the modules must be installed

You own no steps; the substance lives in the `mr-review` skill's modules
and you are their wrapping. The project needs the vendored toolchain
(`/beyonder-dev:beyonder-setup`), concretely:

- `.claude/skills/mr-review/walkthrough.md` — the module you run
- `.claude/skills/mr-review/core.md` — preflight, workspace, cleanup
- `.claude/skills/shared/content-checks.md` — browser discipline and
  screenshot checkpointing, which the module applies
- `.claude/skills/shared/config-discovery.md` — how core.md locates the
  config files, and its § *Layer precedence — project beats generated beats
  vendored* for the case where two of them disagree
- `.claude/skills/mr-review/gitlab.md` / `github.md` — only when you post
  (`--to ticket|mr`): note and image-upload mechanics for that platform

One of the first four missing ⇒ **hard stop** naming the path and
`/beyonder-dev:beyonder-setup`. Improvising the walk without the module is
how this family grew three implementations of the same thing.

## Phase 0 — Intake

**1. The context object — no run without one.** A walkthrough of "the app"
is a fabrication; you document one identified change, and you never guess
which. The argument names it:

- **branch** (default) — no argument, or a branch name: the checked-out
  branch against the base branch from `.claude/beyonder/workflow.md`
  (`git diff $(git merge-base HEAD origin/<base>)`). Nothing is fetched,
  stashed or checked out — the tree is read and browsed, and no git host is
  needed at all. The ticket is best effort here (resolved from the branch
  name per the config's Ticket pattern); none found ⇒ walk the configured
  Flows the diff touches and say the ticket was unavailable.
- **ticket** — a ticket id: fetch it through `workflow.md`'s `## Ticket
  source`; its branch (per the config's Ticket pattern) gives the diff, and
  its acceptance criteria describe the **route** through the feature — a
  route, never criteria; judging them is `content-review`'s job.
- **MR/PR** — a number, `!123`, a URL, or a ticket id that resolves to
  exactly one open MR: its head against its target branch, checked out per
  core.md's Gather step (a worktree, never the dev's tree).

On the base branch with no diff, or an argument that resolves to none of
the three ⇒ stop and say which. State object and destination in one line
before starting ("Walking <object> → <destination>"), so nobody mistakes
what the report is about.

**2. The destination — `--to`, default `local`.** Where the walkthrough is
filed is a parameter, not a consequence of the object: the same branch
walkthrough can end up in a file, under the ticket, or on the MR.

- **`local`** (default) — `.claude/beyonder/reviews/<run-tag>-walkthrough.md`
  with the screenshots next to it, nothing posted. Default because the
  documentation moment sits **before** the MR: the feature is finished, the
  MR may not exist yet, and publishing is a decision, not a side effect of
  the invocation.
- **`ticket`** — one comment on the context ticket, images uploaded per the
  platform doc.
- **`mr`** — one note on the MR/PR: uploaded images plus the marker footer,
  the same shape `mr-review` posts for its walkthrough phase.

Two rules keep the destination honest:

- The config's **Output** sink can only say *less*: `local` in
  `.claude/beyonder/review.md` means this project does not post, so
  `--to ticket|mr` degrades to the local report with one line saying so.
- A destination without a target — no ticket resolved, no open MR, or
  GitHub, which has no image upload API — never costs the deliverable:
  write the local report, post a text-only comment pointing at it where a
  target existed, and name the fallback in the recap.

**3. The run tag** follows the object, not the destination: `mr-<iid>`,
else the ticket reference (`t-123`) or the sanitized branch name. Report
file, artifact directory and browser session derive from it.

## Phase 1 — The run

1. **[core.md](../mr-review/core.md), Preflight** — walkthrough mode:
   config (hard stop if missing), prerequisites, browser tool (hard stop
   if unavailable), credentials, ticket. Skip learnings; read the stack
   file only for its layer definitions. Only an MR object resolves an IID
   (step 1); posting identity only matters when you post.
2. **core.md, Gather & workspace** — walkthrough mode: metadata and
   checkout for an MR object, the branch or ticket object's diff per Phase
   0 with no checkout at all, then the diff preprocessing into patches +
   manifest (to know which flows the change affects). Skip thread indexes
   and the tier gate.
3. **[walkthrough.md](../mr-review/walkthrough.md)** — the module, which
   has exactly one mode: it documents, it never reviews. Its **abort
   rule** (§ *Abort on the first problem*) is your deliverable's shape —
   the core's deliverable exception points the same way. Output per the
   module's Output section, filed per the destination above.
4. **core.md, Cleanup** — worktree/stash only if you checked out,
   environment teardown, artifact handling, diff directory, terminal
   recap.

Reminders:

- You produce no findings and no verdicts. Someone who wants to know
  whether the feature is *correct* runs `content-review`; someone who
  wants the code judged runs `code-review`. Pointing at those in one
  closing line is welcome; doing their work is not.
- A change with no UI effect at all ⇒ say exactly that (comment or
  terminal, per destination) and stop; that is a valid, honest result.
- The golden rule holds: never ask the user anything mid-run.
