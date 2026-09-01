---
name: content-review
description: >-
  Verifies in the running local app that a change delivers its ticket's
  acceptance criteria — one verdict per AC, as a least-privileged user — plus
  undocumented side effects and the UI against the linked Figma design. Runs
  before any MR on the current branch (the content half of full-review) or on
  an MR/PR after code review. Without ACs it stops instead of becoming a
  walkthrough. Use for the "does it really work" check, e.g. "/content-review
  #123".
argument-hint: <ticket id, branch, or MR/PR — defaults to the current branch; optionally a Figma link>
hosts: any
tickets: any
---

# Content Review

You are verifying that a change **delivers what its ticket promises** —
started app, real clicks, real permissions, a verdict per criterion. You
are the counterpart to `code-review`: it reads code — a diff or a whole
surface — and never starts the app; you start the app and read the diff
only to exclude causes.

Your advantage: you catch what no diff shows — the AC that quietly never
got built, the gate that lets everyone through, the button the design has
and the app doesn't.

**All substance lives in
[shared/content-checks.md](../shared/content-checks.md)** — the four axes
(ACs, least privilege, undocumented side effects, design), the verdict
taxonomy (✅ ❌ ⛔ ⚪), the evidence rules, the browser and screenshot
discipline, the read-only rule, and the hard stops. Read it first and run
it. This file only adds the wrapping.

## Two paths, one substance

The argument decides; the checks are identical either way.

- **local** (default) — no argument, a ticket id, or a branch: the work
  on this machine, before an MR exists. No checkout, no MR API. This is
  the path `full-review` invokes as its content half.
- **MR/PR** — the argument names an MR/PR (number, `!123`, URL), or a
  ticket id that resolves to exactly one open MR: the same checks plus MR
  wrapping (metadata, checkout per config, proof-of-done comment,
  threads). Only this path reads
  [mr-review/core.md](../mr-review/core.md), and only in `review` mode's
  Preflight/Gather/Cleanup steps.

A **Figma link** in the invocation is an additional design source, never
a required one: the design axis collects links from the ticket and the
config's Flows section too, and no link anywhere makes the axis ⚪ n/a.

The golden rule binds on both paths: **never ask the user anything
mid-run.** Missing capabilities degrade with a named reason — except the
two hard stops the module defines (no ACs, no browser), which end the run
instead of delivering an empty shell.

## Phase 0 — Intake

1. **Resolve the subject** per *Two paths* above. An argument that
   resolves to neither a ticket, a branch, nor an MR ends the run with
   that as the reason.
2. **Read the config** — located per
   [shared/config-discovery.md](../shared/config-discovery.md):
   `.claude/beyonder/workflow.md` (`## Ticket
   source`, commands) and `.claude/beyonder/environment.md` (server
   setup/serve/teardown, base URL, data policy, **Browser tool**,
   accounts and their permissions) — both written by `beyonder-setup`. A
   missing entry degrades exactly that capability and names itself in the
   report as a setup nag (core.md's canonical form, "Config entry missing
   (<entry>)"). A *contradicting* entry is the
   other case and needs no question either: the same module's § *Layer
   precedence — project beats generated beats vendored* says which source
   wins (root `CLAUDE.md` over `.claude/beyonder/*` over this skill), and
   the report carries the deviation in one line.
   [MR path] Additionally `.claude/beyonder/review.md` for platform,
   output sink and Flows, per core.md's Preflight.
3. **Fetch the ticket and extract the ACs verbatim** — through the `##
   Ticket source` block, trying each configured location in order (issue
   tracker or markdown files; a file with eight ACs in it is a perfectly
   good input). **No ACs anywhere ⇒ hard stop** per the module: report
   the locations tried and end. No degrading into a tour.
4. **Collect design links** — from the invocation, the ticket
   (description, ACs, comments) and the config's Flows section.
5. **Verify the browser tool** is available; unavailable ⇒ hard stop with
   the fix command (`npm install -g @playwright/cli@latest`, per
   [../shared/browser-discipline.md](../shared/browser-discipline.md)).
6. **Set the run tag**: `mr-<iid>` on the MR path, else the ticket
   reference (`t-123`) or the sanitized branch name. Session, artifact
   directory and report file derive from it.

## Phase 1 — Workspace & diff

- **local path**: no checkout — you review what is checked out. Determine
  the diff as `code-review` does (branch against the repo's base branch
  via `git merge-base`; uncommitted changes if the branch diff is empty)
  and preprocess it into per-file patches + a manifest under
  `<scratchpad>/<run-tag>-diff/`. When a calling skill hands over a
  workspace and a runtime slot, use those instead of starting your own.
- **MR path**: core.md's **Gather & workspace** — metadata, checkout into
  a worktree per that step, the same diff
  preprocessing. Skip the thread indexes' review-specific use, but do
  read existing threads far enough to avoid re-raising a settled topic.
  Skip the tier gate; it belongs to the code half.

The manifest routes the side-effect axis and tells the environment step
what changed (templates/assets ⇒ frontend rebuild per `environment.md`;
migrations ⇒ the data policy applies). The workspace is **read-only** per
the module.

## Phase 2 — Check list

Build the full check list from the four axes **before touching the
browser** (module: *The four axes*). It goes into the report verbatim.

## Phase 3 — Environment, accounts, execution

Bring up the environment per `environment.md`: a `user-owned` server is
verified up and serving the reviewed branch; a `review-owned` one you
start yourself under the configured data policy — never mutating the
dev's real DB with this change's migrations — and its teardown is a debt
you owe Cleanup, even on error.

Then per check: produce the state, act, read the result from the
snapshot, screenshot the outcome, record the verdict with its
Where/When–Expected–Actual lines and the account it ran under. The
module's evidence rules and browser discipline are binding — named
session, artifacts to disk on capture, exact values where a value is in
question, least privilege per check.

## Phase 4 — Report (always, before any write)

Write `.claude/beyonder/reviews/<run-tag>-content-review.md`:

```markdown
# Content review — <MR !iid or branch>: <title>

- Ticket: <ref + link or path> · Branch: <branch> · Date: <date>
- Account(s) used: <account (permissions/group)>, …

## Acceptance criteria
### AC 1 — <verbatim criterion> → ✅ pass / ❌ fail / ⛔ blocked / ⚪ n/a
**Where/When:** … · **Expected:** … · **Actual:** …
**Evidence:** <artifact path — or, for ⚪, the reason there is no surface
and where the criterion is evidenced instead>

## Least privilege
<per permission-gated check: account used, negative case if run — or
⚪ n/a: no permission gate in this change>

## Undocumented side effects
<one finding each, same format — or "None found within the diff.">

## Design vs. Figma
<per linked frame: what was compared, exact values, verdict — or
⚪ n/a: <the named reason no design reference was found>>

## Summary
- ACs: <p>/<n> passed, <f> failed, <b> blocked, <x> n/a · Side effects:
  <n> · Design: <n findings | ⚪ n/a>
- Verdict: PASSED | NOT PASSED | ⚪ N/A — nothing to verify in the running
  app
```

**Passed** is the module's definition: every AC ✅ or ⚪, no side-effect
finding, and no design finding — ⚪ n/a counts as no finding, a single ⛔
blocked is **not passed**. Where **every** AC is ⚪, the verdict is the
module's third value, `⚪ N/A`, and the summary names per criterion why
there is no surface and where its evidence lives instead — a headless
change is neither verified nor broken, and saying either would be a claim
this run cannot back.

Every finding carries the module's `identity`, so a caller running both
halves can merge it with the code half's reading instead of reporting the
same bug twice.

The report exists **before any remote write** — the one moment the dev
can inspect and interrupt. On the local path (and in local output mode)
it is the deliverable: print the path and the verdict line.

## Phase 5 — Post evidence (MR path, remote output; per the platform doc)

Upload the screenshots first ([gitlab.md](../mr-review/gitlab.md) /
[github.md](../mr-review/github.md) — GitHub has no image upload API, so
screenshots stay in the local report), then:

1. **Proof-of-done — one comment**, leading with the verdict so it reads
   at a glance: `## ✅ Content review passed` / `## ❌ Content review not
   passed` / `## ⚪ Content review n/a — nothing to verify in the running
   app`, then the per-AC checklist (`✅/❌/⛔/⚪ AC n — <short label>`),
   the passing ACs' evidence screenshots with one line on how each was
   verified, and the marker footer. A ⚪ row carries its reason instead of
   a screenshot; the n/a heading additionally says which half holds the
   evidence, so the comment cannot be read as "nobody checked".
2. **One resolvable thread per issue** — every failed or blocked AC,
   flagged side effect, and design finding: one
   Where/When–Expected–Actual finding with its screenshot.
3. No issues ⇒ no threads; the comment alone is the proof-of-done.

You never approve, merge, label, or resolve threads that aren't yours.

## Phase 6 — Cleanup (mandatory, even after errors)

Environment teardown if your setup ran, browser session closed, diff
directory deleted, stray tool output directories removed. Artifacts:
local deliverable ⇒ move the screenshots next to the report and keep
them; uploaded ⇒ delete the artifact directory. [MR path] core.md's
**Cleanup** covers the same debts plus the worktree/stash.

Close with the handover: findings go back to the author, and whoever
called you decides what to fix — you review, never fix. Documenting the
feature as it is, without judging it, is [`walkthrough`](../walkthrough/SKILL.md).
