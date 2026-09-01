---
name: full-review
description: >-
  Local pre-MR review of a ticket's implementation: code and content in one
  pass. Runs the code-review passes on the branch diff, then content-review
  against the locally running app — acceptance criteria, the UI against the
  linked design — and reports the merged findings. Without acceptance
  criteria it degrades to code-review. Use when a dev wants the full check
  before the MR, e.g. "full-review #123".
hosts: any
tickets: any
---

# Full Review

You are the last check before work leaves the machine: does the code hold
up, **and** does the feature actually do what the ticket says?
`code-review` answers the first question, `content-review` the second —
you run both and merge what they found.

Your advantage: you catch both kinds of embarrassment before the MR
exists — the bug a reviewer would flag, and the AC that quietly never got
built. And because both halves ran on the same change, a defect they both
hit arrives as one finding with two independent evidences.

## Ground rules

- **Autonomous.** No questions after intake. A dead local environment or
  missing browser tooling degrades exactly that capability and is named
  in the report — the code half always runs.
- **You own no checks.** The code half is
  [`code-review`](../code-review/SKILL.md) (substance in
  [shared/review-passes.md](../shared/review-passes.md)), the content
  half is [`content-review`](../content-review/SKILL.md) on its local
  path (substance in
  [shared/content-checks.md](../shared/content-checks.md)). You
  orchestrate, hand over context, and merge. Never re-implement an axis
  here — a copied axis is how the halves drifted apart in the first
  place.
- **Verify, don't demo.** An AC is met when the behavior it demands was
  observed in the running app. Code that looks like it should work is not
  verified, and the table says so.
- **Changed behavior only.** You verify this ticket's ACs, not the whole
  app.
- **No ACs ⇒ `code-review`.** The degrade triggers on **"no acceptance
  criteria could be resolved"** — never on which tooling is available.
  Resolve the ticket through the project's `## Ticket source` block
  (`.claude/beyonder/workflow.md`) first: a markdown file with eight ACs
  in it is a perfectly good input, and a missing `glab` says nothing
  about whether ACs exist. Only when every configured location comes up
  empty do you say so in one line and run the code half alone — the AC
  table needs ACs, not an API. (This is the caller's side of the content
  module's hard stop: the content half never substitutes a tour for the
  judgment.)

## Phase 0 — Intake

Resolve the **ticket** (argument, or extracted from the branch name per
the project's convention in `.claude/beyonder/workflow.md`); fetch it
through that file's `## Ticket source` block — trying each configured
location in order — and extract user story + ACs. Determine the diff as
`code-review` does. Environment facts — how to start the app, base URL,
test login, **Browser tool** — come from
`.claude/beyonder/environment.md` (written by `beyonder-setup`; found per
[shared/config-discovery.md](../shared/config-discovery.md), which is what
a multi-repo workspace needs since that file may sit above the repo, and
whose § *Layer precedence — project beats generated beats vendored* settles
a config entry that contradicts the project's own hand-written rules); when run
as `implement`'s subagent, reuse the slot the caller hands over
(URLs/ports) instead of starting one, and review its worktrees as one
diff where the change spans several repos. Missing config means browser
verification is skipped and named in the report, not asked about.

A **Figma link** given with your invocation is handed to the content half
as an additional design source; it never replaces the links the ticket
carries, and its absence makes the design axis ⚪ n/a, not blocked.

## Phase 1 — Code half

`code-review` in full (its phases 0–3: deterministic checks, dual bug
pass, stack/convention passes, confidence filter) — **plus the
requirements pass, wired here**: `code-review`'s own local specifics skip
that pass, so this phase runs it itself per
[shared/review-passes.md](../shared/review-passes.md), handing it the
ticket from Phase 0 (the same wiring `mr-review` does in its Phase 4).
Its per-criterion verdicts feed Phase 4's headless rule; "not verifiable
in code" is delegated to the content half. All findings feed the merge.

## Phase 2 — Content half

`content-review` on its **local path** — no MR, no posting. Hand over:
the ticket with its ACs verbatim, the preprocessed diff (manifest +
patch paths), the environment config, the design links including any
Figma link from your invocation, and the runtime slot if you were given
one. It runs the four axes and returns its report with one verdict per
check.

Two things you do **not** do here: re-derive its axes, and paper over its
hard stops. No ACs ⇒ the ground-rule degrade above. No browser tool ⇒ the
content half is skipped with the missing tool **and its install command**
named in the report, and the code half stands alone.

Runtime problems the content half met on the way (console errors, broken
flows adjacent to the change) arrive as findings even where the AC itself
passed — take them into the merge.

## Phase 3 — Merge

The two halves saw the same change from different sides. Reconcile them
per [content-checks.md](../shared/content-checks.md) § *Merging with the
code half*, on the `identity` both modules emit — gist: one finding per
identity, carrying every evidence, nothing discarded. Findings without a
file (an AC met nowhere, a missing state) stay unmergeable by
construction and travel as themselves.

## Phase 4 — Combined report

Terminal report, one message:

1. **Verdict line** — ready for MR / needs work, one-sentence why.
   "Ready" requires both halves: the code half without blocking findings
   and the content half **passed** per the module's own definition
   (content-checks § *Verdict taxonomy* — a single ⛔ does not pass).

   **A headless change is ready too, and the condition is where its
   evidence sits.** When the content half returns the module's third
   verdict — `⚪ n/a`, every AC without a user-observable surface — "Ready"
   is available, but only with the ACs evidenced somewhere: the
   requirements pass wired in Phase 1 returned *met* for every criterion. An AC that is ⚪ in the app **and** "not verifiable
   in code" is verified nowhere: that is "needs work", naming the criterion
   and what would verify it. Without this rule a change with no UI can
   never be ready no matter how well it is tested — 0.5.0's backend ticket
   sat at NOT PASSED with eight ACs and 73 green tests behind it.
2. **AC verdict table** — the content half's, in its taxonomy
   (✅ pass / ❌ fail / ⛔ blocked / ⚪ n/a), one row per criterion with how
   it was verified and one line of evidence — for ⚪, the reason there is no
   surface and the code half's per-AC verdict in its place. You reproduce
   it; you don't define it — the table and its taxonomy belong to
   `content-review`.
3. **Findings** — merged per Phase 3, ordered by severity, each with
   `file:line` where it has one and its evidence(s) labelled by half.
4. **Other axes** — least privilege (accounts used, negative cases),
   undocumented side effects, design vs. Figma or the reason it is ⚪ n/a.
5. **Assumptions & skipped capabilities** — one line each, including any
   missing tool with its install command.
6. **One proposed learning**, where either half produced one — per
   [shared/review-passes.md](../shared/review-passes.md) § *Learnings
   writeback*: at most one, in the learnings file's own bullet form, with
   the target file named. Proposed, never written; the dev's "yes" is what
   makes it a learning. Nothing worth generalizing ⇒ omit the section.

When run as `implement`'s subagent, the report's delivery channel is a
**file, not a message**, per
[shared/subagent-handback.md](../shared/subagent-handback.md): write
exactly this report to the path the caller named
(`tmp/<ticket>/review-round-<N>.md` in the caller's run directory, which
sits outside its worktrees; `tmp/` fallback) — the write is the handover, and the file doubles as the loop's
audit trail. No path named ⇒ write `tmp/review-round-1.md` and say so.
Standalone (terminal output is the deliverable), close with the handover:
push and open the MR; `mr-review` re-verifies at the MR and adds the
walkthrough.
