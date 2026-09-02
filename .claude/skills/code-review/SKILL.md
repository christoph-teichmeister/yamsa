---
name: code-review
description: >-
  Reviews code as written, for bugs and cleanness: the working tree or branch
  diff against the base branch, or a named surface with no diff — a
  directory, a module, a layer. Never starts the app; acceptance criteria and
  design belong to content-review, both halves together are full-review.
  Needs no ticket. Use when code should be judged, e.g. "review my changes"
  or "review our billing module".
argument-hint: <nothing = the branch diff · a branch or commit range · a path, module or layer for a surface review>
hosts: any
tickets: none
---

# Code Review

You review code **as written** — no MR, no running app. Two kinds of
object reach you, and the passes are the same for both:

- a **diff** — the branch a dev is about to push, the working tree
  mid-refactoring, the change they're unsure about. The frequent case.
- a **surface** — "review this part of our app": a directory, a module, a
  layer, a feature path across files. No diff exists and none is needed.

Your advantage on a diff: you find the problems before they cost a review
round trip, and with fresh eyes, because you review the code rather than
your memory of writing it. On a surface you are the only entry point in
this family that can judge code **nobody just touched** — everything else
here needs a change to exist first.

Which review is this: **you** judge code as written, changed or not ·
**`full-review`** adds "does it do what the ticket says", so it needs ACs
and a running app and therefore a change — there is **no surface
equivalent**, a surface has no ACs and a surface review is code-only by
construction · **`mr-review`** is for when the object is an MR/PR (threads,
posting, walkthrough) · **`content-review`** and **`walkthrough`** are for
when the object is the running app.

## Ground rules

- **Autonomous.** One question is allowed, at intake, and only for an
  ambiguous target (Phase 0). After that none — missing project setup
  degrades gracefully and is named in the report.
- **You never start the app.** No server, no browser, no clicking. You
  judge the code as written — correctness and cleanness — and everything
  that needs a running system belongs to
  [`content-review`](../content-review/SKILL.md) (both halves together:
  `full-review`). Running without a ticket and without ACs is normal
  here, not a degrade.
- **Reviews, never fixes.** You report; the dev decides what to apply.
  (Ask for fixes afterwards and that's a new task, outside this skill.)
  A caller that fixes your findings and re-invokes you — `implement`'s
  review loop — does not violate this: the fixing belongs to the caller,
  and every invocation of you stays a pure review with fresh eyes.
- **The reviewed set is frozen at intake.** For a diff that means changed
  lines only, pre-existing issues out of scope unless the diff makes them
  worse. For a surface it means the **listed files only** — files you
  discover later (a caller, an importer, a subclass) are *evidence*, read
  to establish or refute a finding, never new scope. A scope that grows
  while the run is going is how a surface review becomes endless and
  finds things at random.
- **A null finding needs a counter-probe.** "Nothing here validates X" is
  the easiest mistake this skill can make, and the surface target invites
  it: a grep with no match shows that one spelling is absent, not that the
  thing is missing. Verify through the *effect* the thing would have — the
  router's endpoint inventory, the caller, the response header, the test —
  before writing it down. Where the counter-probe doesn't carry, the
  sentence is "not found", not "does not exist", and it travels as an open
  question rather than a finding.
- **Project setup is optional but binding.** If `.claude/beyonder/`
  exists, its `stack.md` checklists and both learnings layers
  (project `learnings.md` + `~/.claude/beyonder/learnings.md`) bind
  this review exactly as they bind `mr-review` — one central place to
  tune, both skills follow. Missing ⇒ generic passes only, plus the setup
  nag from mr-review's core.md ("No stack/learnings setup", `step 3`).
- **Token discipline** as in mr-review's core: the reviewed set lives on
  disk, never in a prompt — a diff as per-file patches under
  `<scratchpad>/<run-tag>-diff/` plus a manifest, a surface as the frozen
  file list in that manifest (no patches: subagents read the files
  themselves). Bug passes run on the judgment tier (inherit the session
  model), checklist passes may run a tier cheaper (mr-review core's model
  table is the single source for concrete names); more than a handful of
  findings comes back per
  [../shared/subagent-handback.md](../shared/subagent-handback.md).
  Delete the scratch directories afterwards.

## Phase 0 — Intake

**1. The target — resolved, never guessed.**

- **diff** (default) — no argument, `staged`, a branch name, a commit
  range, a base ref: recognized because the argument resolves as a git
  revision (`git rev-parse --verify`). No argument ⇒ the branch diff
  against the repo's base branch (`git merge-base`), uncommitted changes
  if that diff is empty. Strip noise (lockfiles, generated/vendored code,
  formatting-only files) as mr-review does.
- **surface** — a path, glob or directory `git ls-files` resolves, or
  prose naming a part of the app ("the permission layer", "everything
  under checkout", "the invoice PDF path"). Its file set is built per
  *Surface targets* below.

**Ambiguity is one question, asked once.** An argument that resolves as
both — a branch named `api` next to a directory `api/` — gets a single
sentence with a recommendation ("`api` is both a branch and a directory.
Review the surface `api/`? Recommendation: yes — the branch review is
`code-review` with no argument."). An argument that resolves as neither,
and prose that names no findable part of the repo, ends the run with that
as the reason. Nothing else in this run is a question.

**2. State the resolution in one line** before any pass: `Reviewing <diff
| surface> <target> — <n> files, <diffstat | lines>`. Nobody should have
to infer from the findings what was reviewed.

**3. The run tag** — the sanitized branch name for a diff, the sanitized
target for a surface (`surface-apps-billing`). Manifest, scratch
directory and report file derive from it.

## Surface targets — what stands in for the diff

A diff delivers three things at once: a scope boundary, the author's
intent, and a priority order ("what was just touched matters"). A surface
delivers none of them, so each gets a named substitute — and all three are
fixed at intake, before a single pass runs.

**Scope — the frozen file list.** Two shapes, and neither leaves it to
taste:

- **bounded** — a path, glob or directory: the set is `git ls-files` over
  it, minus the noise categories the diff preprocessing already defines
  (generated, vendored, lockfiles, snapshots, binaries).
- **traced** — prose naming a feature path or layer: start at the entry
  points the words name (route, handler, command, component), follow the
  **callee** direction file by file while a file still belongs to what
  was named, and stop at the framework boundary. Never follow callers —
  that direction has no boundary. Every traced file carries the one-line
  reason it is in the set.

A surface over about **40 files or 5,000 lines** is not reviewed thinner,
it is **cut**: split the list along the surface's own structure
(subpackage, layer, feature slice), review the groups in the risk order
below until the budget is spent, and name the untouched groups in the
report with the invocation that covers each. A report that says which
third of a layer it read is honest; one that read all of it at a quarter
of the depth is not.

**Yardstick — what this code is supposed to be.** Resolve it from
evidence, in this order: the binding docs the config points at plus
`stack.md`'s layer definitions · the surface's own tests, because what the
suite asserts is the contract the team actually wrote down · docstrings
and module READMEs · the words of the invocation ("review the *permission*
layer" says what to judge it as). It goes into the report as one line.
**No yardstick found ⇒ no design findings**, defects only: without a
stated contract, "this should be structured differently" is taste, and a
surface review that ships forty of those gets ignored, rightly.

**Risk order — what recency did.** Compute it from facts, not impressions:
sensitive files first (the tier gate's categories plus whatever `stack.md`
marks critical), then **churn** — `git log --format= --name-only <since>
-- <set> | sort | uniq -c | sort -rn`, because the files the team keeps
reopening are where its bugs live — then fan-in (how many files import
it), size as the tiebreaker. The order goes into the report: the reader
has to know what the run reached first, and where the budget ran out, what
it never reached at all.

## Phase 1 — Deterministic checks

The deterministic checks from
[../shared/review-passes.md](../shared/review-passes.md) — referenced
paths exist, emitted events have consumers, secrets scan (its hits are
never filtered) — run over the reviewed set, whichever kind it is. Plus:
run the project's lint command (from `.claude/beyonder/workflow.md`) if
one is configured, honoring its `baseline:` per
[../shared/command-baselines.md](../shared/command-baselines.md) — report
only, no auto-fix. The baseline rule earns its keep on a surface: a
`dirty:N` tool is the team's standing decision not to enforce it, and
re-raising its pre-existing violations is the noise that makes a surface
report unreadable.

## Phase 2 — Review passes

Run the passes per
[../shared/review-passes.md](../shared/review-passes.md) — subagent
mechanics, finding format, coverage manifests and the pass definitions all
live in that one module; `mr-review` runs the same one, so review behavior
is tuned in exactly one place. Local specifics: **skip the requirements
pass** — verifying the ticket is never this skill's job; the composing
callers (`full-review` Phase 1, `mr-review` Phase 4) wire that pass
themselves in their own phase lists.
A surface set never takes the trivial tier (module: *Tier gate*).

**When is a surface review done?** Not at a round cap. The frozen file
list × the applicable concerns is a **finite grid**, and the run ends when
every cell carries an entry in some coverage manifest — examined, or
skipped with its reason. Silence stays a gap: an uncovered cell gets a
focused follow-up agent on the same tier, exactly as the module
prescribes. Those follow-ups terminate on **finding identity** (module:
*Finding identity*) — the criterion `implement`'s review loop stops on: a
sweep that returns no identity the set doesn't already hold ends the
sweeping. The grid ends the run, identity ends the sweeps, and the report
names any cell that stayed empty.

## Phase 3 — Filter & report

Filter per the module's confidence filter — truth × relevance,
hard-eligibility, nitpick cap (default 3; on a surface it applies **per
group**, so one module's bikeshedding can't silence another's).

Two report shapes, because forty findings and four are different
deliverables:

- **diff** — the terminal report, ordered by severity: one block per
  finding (`file:line` · label · body · suggested fix as a diff snippet
  where it fits), the deterministic-check results and what was validated,
  skipped capabilities and assumptions one line each, and a verdict line
  (ready to push / needs work) with the one-sentence why.
- **surface** — write
  `.claude/beyonder/reviews/<run-tag>-code-review.md` and print its path
  plus the state line and the top findings. A surface review's output is a
  work list that outlives the session; a terminal dump of it is lost by
  the next command.

The surface report is what keeps a large finding count addressable:

1. **Grouped by the surface's own structure**, groups in the risk order
   from intake, findings within a group by severity — a surface is worked
   through file by file, so a flat severity list across the whole layer is
   unusable. Both orders are stated.
2. **Fix set and raise set** — the split
   [`implement`](../implement/SKILL.md)'s review loop applies to review
   output, and the reason forty findings stay workable: *fix* = truth
   established by reading the code **and** the correct behavior follows
   from the yardstick, a documented convention or an existing house
   pattern; *raise* = everything else, each carrying why it wasn't settled
   (**unverified** — plausible, not established; or **judgment** — real,
   but the fix is a product decision, an architecture trade-off, or a
   refactor beyond any one ticket). Neither set is silently applied or
   silently dropped.
3. **A state line instead of a verdict** — `<n> findings across <m> of
   <k> files · fix <a> / raise <b> · coverage complete | budget spent
   after group <x>` plus one sentence on the surface's condition, and one
   line each for yardstick, risk order and untouched groups. There is no
   gate here to pass, and a "ready" line would read as an approval nobody
   asked for.

**One proposed learning, where the run produced one** — last block before
the handover, per
[../shared/review-passes.md](../shared/review-passes.md) § *Learnings
writeback*: its three tests, the file's own bullet form, the target file,
and the cap of one. You propose it; you never write it. Most runs produce
none, and saying nothing is the correct output then.

Close with the handover. Diff: fix what you accept, then `full-review` for
the AC check, or push and let `mr-review` take over. Surface: the fix set
is work, the raise set is decisions for the team — nothing here is pushed
anywhere, and a decision that gets made is recorded with `adr`.
