# Shared module — content checks

Not a skill entry. This module is the **single source for how a change
gets verified in the running app** — the axes, the verdict taxonomy, the
evidence rules, this family's browser and screenshot conventions (on top
of [browser-discipline.md](browser-discipline.md), which holds the rules
every browser-driving skill obeys), and the read-only
rule. `content-review` runs it (standalone or as the content half of a
review); `full-review` gets the content half by invoking that skill, and
`mr-review` gets it through `full-review`. Change verification behavior
here, and every entry point follows.

It is the counterpart to [review-passes.md](review-passes.md): that
module reviews the **code**, this one reviews the **running system**.
Neither reaches into the other — `code-review` never starts the app,
this module never reviews code quality.

Callers differ only in wrapping: the MR path adds MR context (IID,
proof-of-done comment, threads), the standalone path writes a local
report. Nothing in this file depends on an MR existing.

## Inputs (provided by the caller)

1. **The acceptance criteria, verbatim** — from the ticket resolved
   through the project's `## Ticket source` block
   (`.claude/beyonder/workflow.md`). **Load-bearing: no ACs, no run.**
   Without a measuring stick there is nothing to judge, and a run that
   substitutes a tour for the judgment is a walkthrough wearing a
   review's name. Stop and report that as the reason (see *Hard stop*).
2. **The diff, preprocessed** — per-file patch files + a manifest
   (diffstat, per-file layer and flags), as
   [review-passes.md](review-passes.md) defines them for the **diff** shape
   of its reviewed set. That shape is the only one this module takes: the
   side-effect axis is bounded by the change, and the surface shape has no
   change boundary to bound it with. Routes the
   side-effect axis and tells the environment step what changed
   (templates/assets ⇒ frontend rebuild; migrations ⇒ the data policy
   applies).
3. **Environment facts** from `.claude/beyonder/environment.md`: how to
   start the app, base URL, data policy, browser tool, and the accounts
   with their permissions. A missing browser tool is a hard stop — every
   axis here is observed in the app.
4. **Design references** (optional): Figma links the caller collected —
   from the ticket (description, ACs, comments), the config's Flows
   section, and any link handed over with the invocation. Their absence
   makes the design axis `n/a`, never blocked.
5. **A run tag** — `mr-<iid>` on the MR path, otherwise the ticket
   reference or the branch name. Everything this module names per run
   (browser session, artifact directory, report file) derives from it.

## The four axes

Each axis produces checks, each check ends in exactly one verdict. Build
the whole check list **before touching the browser** — it goes into the
report verbatim, and the golden rule makes it output, never a question.

1. **Acceptance criteria** — one check per criterion: entry point
   (URL/action), the expected result **quoted from the AC**, and whether
   it is permission-gated (read the gate from the changed code). Verified
   by observing the behavior in the app; a passing test is corroboration,
   never a substitute for the observation. The one criterion that cannot be
   observed is the one with nothing to observe — see the taxonomy's ⚪ and
   the three conditions that establish it.
2. **Least privilege** — not a separate check list but the account rule
   every other check obeys, and reported as its own axis because it is
   what makes a permission-gated pass worth anything. A superuser passes
   a permission-gated AC even when the change forgot to grant the
   permission — a false positive by construction. Exercise each check as
   a regular user holding exactly the required permissions; where cheap,
   also run the negative case as a user who lacks them — the denial is
   the real proof. A superuser is used only when the AC is itself about
   superuser behavior. No suitable account ⇒ the check is **blocked**,
   never silently run as superuser; if a superuser was used to observe a
   happy path anyway, the report flags the possible false positive.
3. **Undocumented side effects** (diff-bounded) — scan only the changed
   files for behavior no AC mentions: altered permission gates or
   redirects, changed data selection (queries, filters, managers),
   visible field/template/form changes, changed defaults or validation,
   side effects on save/signal/service paths. Each becomes its own check
   with its own verdict. **Derived from the diff, verified in the app** —
   that is what separates this axis from a code read, and it is the axis
   that catches the wire-format bug no AC ever mentioned. Read the
   changed files, not their callers; sweeping beyond the diff is the code
   half's business.
4. **Design** (optional) — per linked Figma frame: use the **figma
   skill** for the node map and exact values (copy, states, the tokens
   the design binds), then compare the implemented UI — rendered text and
   states from the page, computed styles via `playwright-cli eval` where
   a value is in question. Exact values on both sides; screenshots are
   evidence, never the measurement. A state the design shows and the app
   lacks (or vice versa) is a finding. **No design reference anywhere ⇒
   the axis is `n/a`**, with that as the named reason.

## Verdict taxonomy (non-negotiable)

Every check ends as exactly one of four:

- **✅ pass** — verified in the app; the criterion is met.
- **❌ fail** — verified, and the criterion is **not** met (actual
  contradicts expected). The author has something to fix.
- **⛔ blocked** — could **not** be verified although there was something
  to verify (no suitable account, unreachable page, unproducible state,
  missing data). Not a code defect — it needs setup or access before it
  can be judged. Blocked is never silently upgraded to pass.
- **⚪ n/a** — there was **nothing to verify**: the subject does not exist
  in this change. No design reference, no permission gate — or, on the AC
  axis, a criterion with **no user-observable surface** (a job that runs on
  a schedule, an API contract no screen consumes, a migration). Not a
  defect and not a setup gap.

**⛔ and ⚪ are not interchangeable** — ⛔ says "I could not judge this",
⚪ says "there is nothing here to judge" — and the AC axis is where the
mix-up is tempting, because both feel like "no screenshot". **⚪ on an
acceptance criterion has to be established, not assumed**; it holds only
when all three do: the AC's own wording names nothing a user sees, the
diff manifest has no changed frontend/template/asset file this AC could
travel through, and no changed UI-reachable route carries it. Any one of
them failing makes it an ordinary AC — ✅, ❌ or ⛔. State the reason per
⚪ AC in one line ("no user-observable surface: nightly job, no screen")
and name where its evidence does live (the code half's requirements pass,
the test suite, the ticket's own definition) — the ⚪ redirects the burden
of proof, never dismisses it.

**Passed** means: every AC ✅ **or ⚪**, no side-effect finding, and no
design finding — ⚪ n/a counts as no finding, a single ⛔ blocked is
**not passed**.

**The headless change: `⚪ n/a` is also an overall verdict.** When *every*
AC is ⚪, this module had no subject: the run's verdict is **⚪ n/a —
nothing to verify in the running app**, with the per-AC reasons and the
pointer to where the ACs are actually evidenced. Not a degrade and not a
hard stop — the environment came up, the axes ran, and their honest
result is that this change never reaches a screen. A caller gating on
"passed" reads this verdict per its own rule (`full-review` § *Phase 4*,
`mr-review` § *Phase 8*); no caller may turn it into a permanent
negative — which is exactly what 0.5.0 did to a backend change whose
eight ACs were carried by 73 green tests.

## Hard stop (no substitutes)

Two conditions end the run before any check:

- **No acceptance criteria** could be resolved from any configured ticket
  location. Report the locations tried and stop. Do **not** degrade into
  a walkthrough, a code read, or a "here is what the diff seems to do" —
  the caller decides what to do without a measuring stick (`full-review`
  runs its code half alone with one line of reason).
- **No browser tool** available (`.claude/beyonder/environment.md` →
  Browser tool), or the environment cannot be brought up. Every axis
  here is observed in the running app; there is no paper version of this
  deliverable. Name the exact missing piece and its fix command.

Everything else degrades: a single unreachable page is one ⛔ check, not
the end of the run.

## Read-only in the reviewed workspace

**Binding for every caller.** The checkout under review is read-only:
never edit, fix, format, commit, or `git`-mutate it, and never write
report files, screenshots, notes or scratch files into it. This holds
whether the workspace is a worktree, the dev's own tree (in-place
checkout), or the tree a calling skill handed over.

Two exceptions, both narrow:

- **State the feature itself creates.** Producing test data through the
  app's own UI, and whatever the app writes to its database as a result,
  is the check, not a violation — under the data policy from
  `environment.md`, never against the dev's real DB.
- **Commands the environment config prescribes** (setup, serve,
  teardown, fixture install) run as configured, including the build
  artifacts they drop.

Everything you produce lives **outside** the reviewed workspace: the
report under `.claude/beyonder/reviews/` in the invoking checkout,
artifacts under `<scratchpad>/<run-tag>-artifacts/`. A found defect is a
finding, never a fix — the fixing belongs to whoever called you.

(This rule lives here, in the module, because it holds for every caller.
A read-only rule that only exists in one caller's briefing is a rule the
next caller will break.)

## Evidence rules

- **Observed, not inferred.** A check passes when you saw the behavior it
  demands. Code that looks like it should work is not verified, and the
  verdict says so.
- **Every outcome carries evidence** — pass, fail and blocked alike. A
  fail without evidence is an opinion; a blocked without evidence is an
  excuse.
- **Three labelled lines per finding**, in the configured language, each
  but the last ending with two trailing spaces (markdown hard break):

  ```text
  **Where/When:** I click the blue button on a full-moon night.
  **Expected:** A werewolf emerges.
  **Actual:** Nothing happens.
  ```

- **Exact values where a value is in question** — rendered text and
  states read from the page, computed styles via `playwright-cli eval`.
  Screenshots prove that a state existed; they never measure it.
- **An empty state is not the end of a check.** If the seed data doesn't
  exercise the change, create the data through the feature's own UI, then
  verify the full loop against it: save, reload, filters, derived values,
  live updates. Most runtime defects live behind the empty state.
- **Distrust missing feedback.** If the change promises something visible
  and the network call succeeds but nothing renders, that is a ❌ to
  root-cause, not a pass — a 200 is not the feature.
- **Code only to exclude causes.** Reading the changed code to see
  whether a failure is the change's fault or a missing fixture is part of
  the job; judging that code is not. Anything you notice about code
  quality on the way belongs to the code half, not to your verdicts.

## Browser discipline & screenshot checkpointing

The general rules — named session bound to the run's identity, the lock
convention on a browser that cannot be isolated, artifacts checkpointed to
disk as they are taken, and which directories may age — live in
[browser-discipline.md](browser-discipline.md). Read it; what follows is
only what this module binds on top.

- **The run's session name is `-s=<run-tag>-content`.** A singleton
  browser (Chrome MCP, CDP attach) cannot be isolated that way, so
  contention on the lock (`tmp/browser.lock`) degrades the affected
  checks with a named reason instead of fighting over the tab.
- **The run's artifact directory is `<scratchpad>/<run-tag>-artifacts/`**
  — created first, kept outside the reviewed workspace so cleanup can't
  collide with `git worktree remove`, and every capture goes there the
  moment it is taken, with an explicit `--filename=`. Name them
  `<axis>-<n>-<slug>.png` — `ac-3-permission-denied.png`,
  `design-1-empty-state.png`. Never leave a screenshot a report links in
  the browser CLI's own `.playwright-cli/`: that directory is aged out by
  the committed SessionEnd hook, and a verdict's evidence is not
  something that may expire.
- **Re-login to switch accounts**; record which account each check ran
  under, because the least-privilege axis is only as good as that record.
- Consult `console` / `requests` whenever an outcome is unclear — an
  unexplained outcome is not a verdict.

## Finding identity (shared with the code half)

Every finding carries the same `identity` as a code finding — file plus
the **specific defect**, normalized, never the line number — per
[review-passes.md](review-passes.md)'s *Finding identity*. This is what
makes merging possible: when the code half read a defect and this module
observed it, they carry the same identity, and the caller emits **one**
finding with **both** evidences instead of two entries about one bug.
That combination is the strongest evidence class a report can have; do
not let it dissolve into a deduplication.

Where a finding has no file — an AC that is met nowhere, a missing state
— the identity is the axis plus the criterion, and it stays unmergeable
by construction. That is correct: nothing in the code half can be the
same finding.

### Merging with the code half (for callers running both)

`full-review` and `mr-review` run both halves on the same change and must
reconcile them before reporting. The rule is the same for both, so it
lives here:

- **Same identity in both halves ⇒ ONE finding with BOTH evidences** —
  read in the code *and* observed in the running system. Say both, in
  that one entry: it is the strongest evidence class a report can carry,
  and it is what makes a finding hard to wave away.
- **Only one half saw it ⇒ one finding with that half's evidence.** A
  code finding the app didn't show is not weaker for it (unreached path,
  race, boundary no check hit) — never drop it for lack of a screenshot,
  and never let the other half's silence read as a contradiction.
- **The halves genuinely disagree** (the code says the gate is there, the
  app lets the user through) ⇒ keep both statements in one finding and
  say which one was verified how. The disagreement *is* the finding.
- **Merging is not deduplication.** Nothing is discarded here: two
  entries become one richer entry, or they stay two.

A rule the team taught you while you were verifying — "that empty state is
intentional", "we never gate this screen" — travels the same way as the code
half's: [review-passes.md](review-passes.md) § *Learnings writeback* owns
the three tests, the form, the target file and the one-per-run cap. Nothing
in this module writes those files.
