# Shared module — review passes

Not a skill entry. This module is the **single source for how code gets
reviewed** in this toolchain — the pass definitions, the finding format,
the deterministic checks, the confidence filter, and the way a learning
gets back into the learnings files. `mr-review` (Phases 3/4/8/9) and
`code-review` (and through it `full-review`) run it; change review behavior
here, and every entry point follows.

Its counterpart is [content-checks.md](content-checks.md), the single
source for how the **running app** gets verified. The two never reach
into each other: nothing here starts a server, nothing there judges code
quality. Callers that run both (`full-review`, `mr-review`) merge the
findings per that module's *Merging with the code half*.

Callers differ only in wrapping: `mr-review` adds MR context (thread
index, ticket, posting), `code-review` runs bare — on a local diff, or on
a surface with no diff at all. Model routing uses the tier names below;
concrete model names live only in mr-review's `core.md` table.

## Inputs (provided by the caller)

1. **The reviewed set, preprocessed** — whatever the caller put under
   review, resolved before any pass and not growing during one. Two
   shapes:
   - **a diff**: per-file patch files + a manifest (diffstat, per-file
     layer and flags; noise and formatting-only files already excluded).
   - **a surface** (`code-review`'s surface target: a directory, module or
     layer, no diff involved): the frozen file list in the manifest, with
     the same per-file layer and flags and no patch files.

   Either way subagents receive the manifest and the paths, never pasted
   diff or file text. Everywhere below, *the reviewed set* means whichever
   of the two the caller handed over.
2. `stack.md` and both learnings layers from `.claude/beyonder/`
   (either may be missing ⇒ skip what depends on it, tell the caller).
3. Optional: a **ticket** (user story + ACs) — enables the requirements
   pass. Optional: a **thread/topic index** (mr-review) — passed through
   to subagents to avoid re-flagging settled topics.

## Deterministic checks (cheap, every run, before any pass)

- Every file, asset, template path, route/URL name, and identifier the
  reviewed set *references* must exist in the branch (`git ls-files` /
  `grep`). A missing referenced file is a finding, not a note.
- Every event name and payload key the reviewed set *emits* must have a
  consumer somewhere in the branch (`grep`).
- **Secrets scan** over the reviewed set: private-key blocks
  (`-----BEGIN … PRIVATE KEY`), cloud/API key signatures
  (`AKIA[0-9A-Z]{16}`, `ghp_…`, `glpat-…`), hardcoded passwords/tokens
  in code or CI config, newly added `.env`/credential files. Any hit is
  a highest-severity finding — never subject to the confidence filter
  or the nitpick budget.

## Tier gate

**Trivial** — ≤ ~50 changed lines across ≤ 5 files AND no sensitive file
(auth/permissions, payments, crypto/secrets, migrations, CI/deploy, plus
anything the stack file marks critical): run ONE combined judgment-tier
subagent covering the bug concerns, the applicable stack checklists,
conventions, the reuse-and-minimality concerns (pass 6), and (with a
ticket) the per-AC verdicts — same finding
format and coverage manifest, no dual bug pass. Anything bigger, and any
sensitive-file diff regardless of size, is **full** and runs the passes
below. A **surface** set is never trivial — the gate reads changed lines,
and a set with no diff has none to be small. Record the tier and its
reason for the caller's summary.

## The passes (full tier; parallel subagents)

Each subagent gets the manifest, the patch paths for its files, the
learnings, (passes 2–4) the stack file, and — where its output is more
than a handful of findings — a **handback path** to write per
[subagent-handback.md](subagent-handback.md). Each returns candidate
findings as
`{file, line, identity, label, severity, body, suggestion?,
confidence-rationale}`
(body ≤ 80 words, no narrative around the list) **plus a coverage
manifest**: which files of the reviewed set and which concern types it
examined, and which it skipped (why). Silence is a gap, not a clean bill —
a file or applicable concern in no manifest gets a focused follow-up agent
on the same tier before filtering.

1. **Bug pass** (always; judgment tier — NEVER lower, recall is the
   product) — logic errors, edge cases, error handling, security
   (missing auth/permission checks on new endpoints, injection, secrets,
   unescaped user-controlled strings reaching HTML/JS). For
   user-supplied parameters check *magnitude*, not just format; for
   async request/response code check ordering (can a stale in-flight
   response overwrite a newer one?). **The reviewed set only** — on a diff
   that means changed lines, and pre-existing issues are out of scope
   unless the diff makes them worse; on a surface it means the listed
   files, where "pre-existing" has no meaning and the defects that were
   always there are the point. Run as **two independent subagents** (no
   shared candidates) and union the results.
2. **Backend pass** (if the stack file has a backend section and the
   reviewed set has backend files; checklist tier) — the stack file's
   backend checklist against them.
3. **Frontend pass** (same conditions for frontend; checklist tier) —
   the stack file's frontend checklist, plus always: accessibility
   (interactive elements without roles/labels, removed focus styles
   without replacement, ARIA attributes without the matching role).
4. **Convention pass** (checklist tier) — compliance with the binding
   docs the config points to and with both learnings layers.
5. **Requirements pass** (only with a ticket; judgment tier) — does the
   diff satisfy the user story and each AC? Per-AC verdict (met / not
   met / not verifiable in code — the caller decides what happens to
   those) plus findings for violated or silently reinterpreted ACs and
   undocumented side effects beyond the ticket's scope.
6. **Reuse & minimality pass** (always; judgment tier) — the one pass
   that reads the reviewed set **against the codebase** instead of only
   in itself. Agentic diffs run measurably larger than human ones, and
   the best-evidenced cause is duplication instead of reuse — this pass
   hunts exactly that:
   - **reimplemented existing code** — a helper, validator, component or
     query the codebase already has; the finding quotes the existing
     code's **path**, or it is not a finding;
   - **scaffolding leftovers** — repro scripts, debug output,
     commented-out attempts, helpers nothing calls;
   - **deletable code** — additions the change does not need, removable
     without behavior change (the caller's fix loop and its tests prove
     the equivalence — this pass only claims it);
   - **comments against the project's comment policy** (the
     `## Comment policy` section of the project's knowledge file —
     `AGENTS.md`, or `CLAUDE.md` where the project keeps it there), checked in
     both directions: narrative noise *and* missing constraint/why
     comments. A written policy makes these findings hard-eligible; no
     policy ⇒ skip the comment check and tell the caller.

   On a diff, "the codebase" means the checked-out branch beyond the
   changed lines — the one pass whose evidence lives outside the diff by
   design. On a surface, duplication, dead code and policy violations
   inside the listed files are the same finding classes. Fixes travel
   through the caller's normal fix loop; the gates prove behavior is
   preserved.

## Confidence filter

Score every candidate on TWO axes, never blended:

- **Truth (0–100)** — factually real? Verify against the checked-out
  code (targeted reads of the finding's region), not the diff alone. A
  statically provable fact scores ~100 regardless of how minor it feels.
- **Relevance** — would a senior engineer flag it? A documented
  convention or learning makes a violation relevant *by definition*;
  low relevance = matches an existing house pattern, separate-ticket
  refactoring, purely hypothetical impact. One carve-out, because pass 6
  exists: simplification of the **diff's own additions** is in scope and
  relevant — "separate-ticket refactoring" is about pre-existing code,
  never about lines this change introduced.

Drop candidates you refuted or that are genuinely irrelevant. Findings
that survive this filter are relevant **by construction** — a caller
deciding what to do with them is choosing among relevant findings, never
re-litigating whether they matter.
**Hard-eligible** findings — provably true + backed by a documented
project convention — always surface as first-class findings, never
folded away. Cap nitpick-level findings at the caller's budget (default
3); fold the rest into one line. How surviving findings are *delivered*
(posted threads vs. terminal report, threshold modes) is the caller's
business.

## Finding identity

Every finding carries an `identity`: the file plus the **specific
defect**, normalized — never the line number, which shifts the moment a
fix lands. Two candidates are the same finding when they name the same
defect in the same file, even from different passes in different words;
the same label on two genuinely different defects in one file is two
findings.

Three things depend on this and would otherwise each invent their own
rule: the union of the dual bug pass, `mr-review`'s dedup against
already-posted threads, and a caller's re-review deciding whether a
finding is *new* (`implement`'s review loop terminates on exactly that
question). Emit it per finding so no caller has to re-derive it.

## Learnings writeback

Both learnings layers (Inputs, item 2) are read on every run and bind the
convention pass. The way back is this section — one rule for every entry
point, the local paths (`code-review`, `full-review`, `implement`'s
review loop) included, so a usable rule a local round formulates never
evaporates for lack of a channel.

**What qualifies.** A learning is a rule for *future* reviews, not a
statement about this change. All three tests have to hold:

1. **It generalizes.** It applies to the next change too. A fact about
   these files is a report line; "we accept this pattern here" is a
   learning.
2. **It is a decision, not a discovery.** Someone with authority over the
   codebase resolved it: a finding rejected with a reason ("intentional",
   "we always do it this way", "don't flag X"), or a review-established
   convention no document carries yet.
3. **No other drawer fits.** A stack-level defect class belongs in
   `stack.md`, a rule the whole team must follow belongs in the project's
   own docs or its hard rules, a fact about the setup belongs in
   `workflow.md`/`environment.md`. Learnings are the residue: taste, and the
   exceptions a checklist would otherwise keep re-flagging.

**Who writes.** The skill **proposes**, a human **confirms**, and only then
does anything get appended. Where the confirmation already exists — a
`mr-review` thread reply teaching the review something (its § *Phase 9 —
Learnings capture*) — the reply *is* the confirmation and the skill
appends. Where it does not, the proposal is the deliverable: **at most one**
candidate, at the end of the report, in the file's own form and ready to
paste, plus the file it belongs in. A subagent never writes to the
learnings files at all — its candidate travels in its handback and the
caller decides whether it survives to the report.

**Form and target.** Append as a dated bullet in the file's existing form
(`- YYYY-MM-DD (<ref>): <learning>`, where `<ref>` is the MR, ticket or
branch the learning came from) to `.claude/beyonder/learnings.md` — or to
`~/.claude/beyonder/learnings.md` when it is clearly project-independent.
Both files stay human-editable: never reformat, reorder or prune them, and
never rewrite a bullet someone else wrote.

**Why the file does not become a bin.** Three limits, and they are the
point of the whole section:

- **One candidate per run, maximum.** A run that proposes five things
  learned nothing; it is describing its findings again.
- **Sharpen before appending.** If a bullet on the same subject exists,
  propose an edit to *that* bullet instead of a second one. Two bullets on
  one subject are how the file stops being read.
- **No unconfirmed writes, ever.** An unconfirmed learning suppresses
  future findings on nobody's authority — the one failure mode of this layer
  that is worse than it staying empty.
