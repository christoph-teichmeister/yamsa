---
name: mr-review
description: >-
  CodeRabbit-style unattended review of a GitLab MR or GitHub PR: code
  review, content review in the running app, and — unless an AC failed — a
  screenshot walkthrough of the feature. Posts everything back as labeled
  threads with one-click suggestions and an AC verdict table. Runs detached
  in its own worktree and slot, so the dev keeps working. Use when asked to
  review an MR/PR, e.g. "/mr-review 123".
argument-hint: <MR IID or URL> [--attached]
hosts: [gitlab, github]
tickets: any
---

# MR Review

You are performing a complete, unattended review of a merge/pull request.

You are `full-review` **plus** a walkthrough **plus** the MR wrapping:
both review halves — code per
[../shared/review-passes.md](../shared/review-passes.md), the running
system per [../shared/content-checks.md](../shared/content-checks.md) —
their merged findings, and then the feature documented for the people who
won't pull the branch. You own none of those checks; you own the wrapping,
the gate between the halves and the walkthrough, and what gets posted.

**Read [core.md](core.md) first and run in `review` mode.** It defines the
binding ground rules — golden rule (never ask the user mid-run), output
language, output sinks, platform docs (gitlab.md/github.md), and the token
discipline incl. the model-tier table — plus the shared Preflight, Gather &
workspace, and Cleanup steps. This file only adds what is review-specific.

Review output per the core Output-sink rules:

- **remote**: threads and summary on the MR/PR itself.
- **local**: a report at `.claude/beyonder/reviews/mr-<iid>.md` — same
  content as a remote review (merged findings ordered by severity with
  `file:line` anchors, label, body, suggestion blocks; validation
  results; the AC verdict table and the other content axes; walkthrough
  with relative-linked screenshots next to the report; summary). The
  content half's own report (`mr-<iid>-content-review.md`) is not written
  separately in this run — its verdicts land here.

This skill is **stack-agnostic**. Everything framework-specific lives in the
project's `.claude/beyonder/stack.md` (written by `beyonder-setup` ③) — the
backend and frontend passes run on its checklists. A project may have no
backend or no frontend; run only the passes whose section exists.

## Isolation & hosting

**Isolation is not decided here — and not in `review.md` either.** Every
run isolates itself, always: own worktree, own runtime slot where the app
is needed, own browser session. The rules are `implement`'s and this skill
inherits them verbatim —
[../implement/SKILL.md](../implement/SKILL.md) § *Isolation — every run
stands alone*: how a slot's `N` is claimed and released, why the toolchain
is never copied into a worktree, where the run's surviving files go, and
what a run does when isolation is provably impossible (work in place,
report it in one line — never a mode chosen in advance). Nothing about it
is a config field; there is nothing to look up.

Everything isolated here is bound to this run's identity, `mr-<iid>`: the
worktree at `<scratchpad>/mr-<iid>` (core.md, *Gather & workspace*), the
`playwright-cli` session `-s=mr-<iid>`, the slot claimed per that section.
No parallel-run recipe in `workflow.md` ⇒ the two app-facing phases
(content half, walkthrough) degrade with that as the reason; the code half
still runs.

**Hosting is what an invocation does decide.** Default: **detached** — this
session's only job is to launch the run as a background agent and hand the
terminal back, because the dev keeps working next to it. The background
agent runs all phases (0–10) unchanged, delivers through the configured
sink, and adds a completion message naming the MR, the verdict line and
where the output landed; it runs Phase 10 itself, also on error. Nothing
waits for the dev.

**`--attached` switches off exactly one thing: the backgrounding.** The
run then happens in this session, phase by phase in front of the dev —
for debugging the review itself, and for a harness that cannot spawn
background agents. A debug flag per invocation, never a project setting,
and it changes **nothing** about isolation: same worktree, same slot, same
named browser session.

## Phase 0 — Preflight

Run the core module's **Preflight** (all steps — review mode uses every
one, including both learnings layers).

## Phase 1 — Gather

Run the core module's **Gather & workspace** (all steps, including the
thread indexes, the checkout, the diff preprocessing into
`<scratchpad>/mr-<iid>-diff/` + `manifest.md`, and the tier gate).

## Phase 2 — Description & change listing

Run the [describe module](describe.md) — an internal module of this skill,
with no entry of its own: description update if empty/trivial; change
listing only if the config's Comments section says so — it opens the
summary/report, never a separate note.

## Phase 3 — Runtime validation

Run inside the review workspace, using the commands from
`.claude/beyonder/workflow.md` (skip whatever is `-`):

1. Validate/build command (+ its `when:` variants if their condition holds)
2. Test command (`targeted:` variant for large diffs)
3. Lint/format command (report only — never auto-fix during a review)
4. Migrations check as configured; never against the dev's real DB.
5. The **deterministic checks** from
   [../shared/review-passes.md](../shared/review-passes.md) —
   referenced paths exist, emitted events have consumers, secrets scan
   (its hits are never filtered).

Failures become findings: broken tests/build ⇒ highest-severity label.
Lint violations that fail a merge-blocking gate (pre-commit hook, CI lint
job) are also highest severity — a red pipeline blocks the merge, whatever
the underlying rule's pettiness; link the failing CI job as evidence if one
exists. Only style output that does NOT block merging competes for the
nitpick budget.

## Phase 4 — Code half: review passes

Run the passes per
[../shared/review-passes.md](../shared/review-passes.md) — tier gate,
subagent mechanics, finding format, coverage manifests, and the pass
definitions (dual bug, backend/frontend, convention, requirements) all
live there. Review behavior is tuned in that one module, for every
entry point (`mr-review` here, `code-review`/`full-review` locally).
MR-specific wiring on top:

- Each subagent additionally gets the **thread index**, so settled
  topics aren't re-flagged.
- The **requirements pass** runs only if a ticket was fetched; its
  "not verifiable in code" verdicts are delegated to the **content half**
  (Phase 5) — that is what it is for. Nothing in this phase starts the
  app. The delegation can come back empty in both directions: a criterion
  the code half calls "not verifiable in code" that the content half marks
  ⚪ (no user-observable surface) is verified **nowhere**, and the summary
  says exactly that per criterion instead of letting the two halves' shrugs
  cancel out.

## Phase 5 — Content half: does it really work?

Run the content checks per
[../shared/content-checks.md](../shared/content-checks.md) — the four
axes (acceptance criteria, least privilege, undocumented side effects,
design vs. the linked Figma frames), the ✅ ❌ ⛔ ⚪ verdict taxonomy, the
evidence rules, the browser discipline and the read-only rule. This is
the same half [`content-review`](../content-review/SKILL.md) runs on its
own; invoking `/content-review <iid>` gives exactly this phase and its
proof-of-done comment, nothing else. **Inside this run there is no
separate proof-of-done comment** — your summary note (Phase 8) carries
the verdicts, and the findings become threads with everything else.

Everything the module needs is already gathered: the ticket's ACs
verbatim (Phase 0), the manifest and patch paths (Phase 1), the
environment config, and the design links — from the ticket, the config's
Flows section, and any Figma link handed over with the invocation. Set
the run tag to `mr-<iid>`.

Two hard stops from the module, resolved the MR way:

- **No ACs resolvable** ⇒ the content half does not run; say so in one
  line in the summary and let the code half stand alone. Never substitute
  the walkthrough for it — a tour is not a verdict.
- **No browser tool** ⇒ same, with the missing tool **and its install
  command** named (`npm install -g @playwright/cli@latest` per
  [../shared/browser-discipline.md](../shared/browser-discipline.md));
  Phase 7 falls away too, since it needs the same browser.

## Phase 6 — Merge the halves

Reconcile the two halves' findings per
[../shared/content-checks.md](../shared/content-checks.md) § *Merging
with the code half*, on the `identity` both modules emit — gist: one
finding per identity, carrying every evidence, nothing discarded; a
merged finding is the strongest thing you can post.

The merged set is what Phase 8 filters and posts. Per-AC verdicts travel
as themselves into the AC status table.

## Phase 7 — Walkthrough (gated)

Run the [walkthrough module](walkthrough.md) — one mode: it documents the
feature, it does not review. Only if the diff affects UI and the browser
tool is available.

**The gate.** The walkthrough starts only if the content half found **no
breaking change**, where

> **breaking change := a ❌ on an acceptance criterion, or a blocker-level
> finding from the code half.**

⛔ **blocked does not count** — a missing test account must not stop the
documentation. ⚪ n/a never counts either. Gate closed ⇒ skip the
walkthrough and say why in one line: documenting a feature that demonstrably
doesn't deliver an AC would publish a picture of something broken.

**Widerspruchsregel — the walkthrough aborts although the gate was open.**
The module aborts on the first problem of any kind. If that happens on an
open gate, the two halves contradict each other, and the contradiction is
the interesting part:

1. Take the abort **as a finding** (the walkthrough's evidence: flow,
   step, expected, actual, screenshot) into the merged set.
2. Re-run the content half **narrowed to that one flow** — same module,
   same accounts, just this route. Anything it uncovers goes into the
   report as a proper verdict, and the walkthrough stays undone (do not
   restart it).
3. It uncovers nothing ⇒ report both statements as they are: the
   walkthrough's abort and the content half's clean verdict on that flow.
   An unexplained contradiction is honest output; a blind retry would
   hide it.

Never re-run the walkthrough hoping it works the second time.

## Phase 8 — Filter, then post

**Confidence filter** per
[../shared/review-passes.md](../shared/review-passes.md): score truth
(0–100) and relevance separately, drop refuted or genuinely irrelevant
candidates, respect hard-eligibility and the nitpick budget (from
config, default 3). Then apply the config's Confidence mode to decide
what becomes a thread:

- `threshold:<n>` (default 80): post a finding as a thread when truth ≥ n
  AND it is relevant; fold the sub-threshold rest into the summary. Drop it
  when truth is far below threshold OR relevance is genuinely low.
- `all-threads`: every relevant finding becomes its own thread, each
  stating its confidence — a human judges relevance. Only drop what you
  yourself refuted.
- `custom:<values>`: as configured.

Hard-eligible findings — provably true + backed by a documented project
convention — are posted as positioned threads, never folded into a
collapsed summary section: threads are resolvable and merge-relevant,
collapsed blocks get ignored. It's fine to note residual uncertainty
*inside* a posted thread (as a `question`) instead of withholding the whole
finding.

**Lint your own suggestions.** Before posting, check every ` ```suggestion `
block against the same conventions and learnings you review by. A fix that
itself violates a documented convention undermines the finding and teaches
the wrong pattern.

**Post** (remote mode; in local mode the identical content goes into the
report):

1. One positioned discussion per surviving finding on the exact diff line.
   Findings on the same topic (e.g. several a11y details) belong in ONE
   thread, anchored at the most representative line — a borderline
   candidate that extends a topic you're posting anyway joins that thread
   instead of being withheld. Format per the config's Comments system —
   default conventional comments with the configured labels; a
   severity/custom system uses its levels instead — with a
   ` ```suggestion ` block whenever the fix fits the commented lines
   (one-click apply).
2. Resolve your own previous threads whose issue the new commits fixed,
   with a short confirming reply before resolving.
3. Reply to threads that ask something you can genuinely resolve (including
   human threads you were not part of) — only when it adds real value,
   never to comment on discussions that are going fine without you.
4. Post the summary note: the change listing (if configured), verdict, the
   **AC status table** (if the content half ran: one row per acceptance
   criterion in the module's taxonomy — ✅ pass / ❌ fail / ⛔ blocked /
   ⚪ n/a — plus how it was verified and one line of evidence; where every
   row is ⚪ the content half's verdict is the module's `⚪ n/a — nothing to
   verify in the running app`, posted as that and not as a failure; the
   table and its taxonomy belong to the content module, you reproduce
   them), the other
   content axes (least privilege, undocumented side effects, design vs.
   Figma or ⚪ n/a with its reason), what was validated (tests/lint/
   migrations with results), the feature walkthrough or the one line why
   it was gated out or aborted, skipped capabilities and why (missing
   tools **with their install command**), folded nitpicks, and any config
   nags collected under the soft-validation/stale-config rules. Merged
   findings state both evidences. End every summary with the standing
   learnings invitation:
   > 💡 Disagree with a finding, or is context missing? Reply directly in
   > the thread — the review picks it up as a learning on its next run.

## Phase 9 — Learnings capture

**What qualifies as a learning, in what form, into which file, and the
limits that keep the file readable** live in
[../shared/review-passes.md](../shared/review-passes.md)
§ *Learnings writeback* — one rule for every entry point. This phase is the
MR-specific part: you are the one entry point where the human confirmation
already exists on the platform, in a thread, which is why you append and
the local skills only propose.

Three capture mechanisms feed the learnings files (remote mode; in local
mode there are no threads to read, so you propose in the report like the
local skills do — one candidate at most — while both files still bind the
review):

1. **Inline** — while reading threads (Phase 1) you may have seen author
   replies that teach a preference: "that's intentional", "we always do it
   this way here", "please don't flag X".
2. **Second pass over your own past threads** — teachings usually arrive
   *after* a run has posted. Right after Phase 1, list the last ~5 MRs this
   skill reviewed (marker footer / own author) and scan your threads there
   for human replies or resolutions-without-fix that haven't been captured
   yet (skip anything already in the learnings files). Do this before
   Phase 4 so fresh learnings bind the current review.
3. **Summary invitation** — the standing footer on every summary (Phase 8)
   tells the team that replying to a thread teaches the review; those
   replies are what mechanisms 1–2 pick up on later runs.

Append per the module's *Form and target*, and say so in your reply to that
thread — the reply is both the confirmation and the receipt. A thread that
teaches nothing generalizable stays a thread; the module's three tests
decide, not the fact that someone replied.

## Phase 10 — Cleanup (mandatory, even after errors)

Run the core module's **Cleanup** — in review mode every debt can apply:
worktree/stash, walkthrough teardown, artifact handling, the diff
directory, stray tool output, and the terminal recap.
