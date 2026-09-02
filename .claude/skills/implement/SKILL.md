---
name: implement
description: >-
  Implements a ticket end to end, autonomously: after a single intake round
  there are no further questions — the dev can switch windows. Follows any
  plan technical-planning left in the ticket and ends with a review-and-fix
  loop. Each run isolates itself in its own branch and worktree, so several
  tickets can be built in parallel. Use when a dev wants a ticket built, e.g.
  "implement #123".
hosts: any
tickets: any
---

# Implement

You are executing the implementation of a ticket, start to finish:
understand, build, test, self-review, commit. The dev hands you the
ticket and walks away — everything after the intake happens without
them, and the report at the end tells them exactly what happened.
While you work, the dev may be planning and implementing the next
ticket in another session; your isolation rules make that safe.

Your advantage: you follow the ticket's plan and the project's
conventions more patiently than a rushed human — and you verify your own
work with fresh eyes (`full-review`) before anyone else sees it.

## Ground rules

- **Autonomous after intake.** One intake round, then not a single
  question. Ambiguities are resolved by the ticket, the plan, the code's
  existing patterns — in that order — and every judgment call is a
  **marked assumption in the report**. A genuine blocker (contradictory
  ACs, dead environment) ends that ticket's run with a precise report,
  never with a mid-run question.
- **The project workflow is law.** `.claude/beyonder/workflow.md` (written
  by `beyonder-setup`, at project level rather than in `~/.claude/`)
  defines base branch, branch
  naming, test runner, QA gates, commit format, push policy, and the
  parallel-run recipe. Find it — and `environment.md`, which in a
  multi-repo workspace may sit a level higher — per
  [../shared/config-discovery.md](../shared/config-discovery.md); don't
  invent a search order per run. Intake reads these files **once** and
  freezes them into the run directory (Phase 0, point 3); after intake
  the frozen copies are the run's only source. No file ⇒ derive defaults from the repo (default
  branch, CI config, CLAUDE.md/AGENTS.md) and list them as assumptions
  at intake — the one moment the dev can still object.
  **Where two sources contradict each other**, that module's § *Layer
  precedence — project beats generated beats vendored* decides — gist:
  the higher layer wins, the deviation is named in one line, and a
  **hard** project rule is a boundary you route around or degrade
  against, never a mid-run question (*Autonomous after intake*, above).
- **Tests must pass.** Run the affected tests after building (the
  workflow's runner); fix failures before review. A test rewritten to
  encode new behavior is fine; a test deleted to go green is not.
- **Build against the review's own checklist.** Phase 2 checks your diff
  against `.claude/beyonder/stack.md` and both learnings layers (project
  `learnings.md` + `~/.claude/beyonder/learnings.md`) — at run time all
  of them from the intake's frozen copies (Phase 0, point 3). Read them
  **before** building, not after: a convention you follow costs nothing,
  the same one found in review costs a fix commit and a re-review round.
  Missing files ⇒ the codebase's existing patterns are the only
  standard, and the report says so.
- **Reuse before writing, strip scaffolding before handing back.**
  Before any new helper, component or query: search for an existing one —
  the review's reuse-&-minimality pass
  ([../shared/review-passes.md](../shared/review-passes.md), pass 6)
  flags a reimplementation with the existing code's path. Debug
  scaffolding (repro scripts, print/log lines, commented-out attempts)
  is removed before the handback, not left for the review to find; and
  comments follow the project's `## Comment policy` (in `AGENTS.md`, or
  `CLAUDE.md` where the project keeps it there) where one exists. This line goes into every build and fix subagent's briefing.
- **Commit, never push** unless the workflow file says otherwise. Stage
  deliberately (no `git add .`); commit messages per the workflow's
  format.
- **Ticket access, snapshots and write safety** per
  [../shared/ticket-writes.md](../shared/ticket-writes.md): resolution
  through the project's `## Ticket source` block (anchored paths included
  — you read that block from a worktree more often than not), the
  tracker binding, the snapshot rule for unversioned ticket files, the
  fence trap. Two deltas of this skill: the **intake confirmation is the
  sanctioned moment** that covers the run's continuous ticket writes
  (tick-offs, Stand lines, watch-outs) — there is no per-write
  confirmation; and **read-only tracker mode** — when the dev forbids
  tracker writes for this run (or the token cannot write), reads still go
  through the tracker and **the run's plan file becomes the write side**:
  tick-offs, Stand lines and watch-outs land in `tmp/<ticket>/plan.md` in
  the run directory, under the same snapshot rule, with the substitution
  named in the report in one line.
- **Never claim what didn't happen.** Test results, review findings, and
  skipped steps appear in the report as they are.
- **Every subagent hands back through a file**, per
  [../shared/subagent-handback.md](../shared/subagent-handback.md): you
  name `tmp/<ticket>/<phase>-<id>.md` in the briefing — the run directory
  from the Isolation rules (point 4), outside every worktree so it
  survives their teardown — the child writes it, you read it when the task
  notification arrives. This binds every
  delegation in this skill — step groups, themes, fix rounds, the
  reviewer — not just the review loop. Agent messaging is best effort and
  fails exactly where these runs live: a parent continued from its
  transcript after a limit is no longer addressable for its running
  children.
- **Subagents run on at most Opus.** Same scope as the rule above — every
  delegation this skill makes: when the session model sits **above** Opus
  (a Mythos-class session), set `model: opus` on the Agent call; on Opus
  or below, omit the param and inherit as always. A long run fans out
  into many subagents, and without the cap each one bills the session
  model's price for work Opus does just as well. The one exception is the
  dev naming a model explicitly for this run — that wins. The reviewer
  subagent inherits the cap naturally: the review family's judgment tier
  reads "inherit the session model" (mr-review core's model table), which
  inside a capped subagent *is* Opus; its checklist/mechanical tiers stay
  cheaper as configured.

## Phase 0 — Intake (the only interactive moment)

1. Resolve the **ticket** from the invocation; ask once if missing.
2. Fetch it **through the project's ticket source** (ground rules):
   description, ACs, comments, linked issues — and **the plan**, if
   `technical-planning` left one (its named defaults: a plan comment on a
   tracker, a `## Plan` section in a ticket file — accept either form
   wherever you find it).
   A reference that resolves in no configured location ends the run with
   that as the reason; a wrong ticket silently built is worse.
3. **Freeze the config — the run's one read of the live files.** Read
   `.claude/beyonder/workflow.md`, `environment.md`, `stack.md`,
   `review.md`, both learnings layers **and `access.local.md`** (where it
   exists) once — located per
   [../shared/config-discovery.md](../shared/config-discovery.md) — copy
   them verbatim into `tmp/<ticket>/config/` — the run directory
   (Isolation, point 4): outside every worktree, untouched by branch
   switches — and from then on **every read goes to the frozen copies**,
   yours and every subagent's alike; briefings name that path, never
   `.claude/beyonder/`. The guarantee this buys: the main checkout is
   the *unstable* source — the dev may switch branches there mid-run,
   and the first full eval run survived exactly such a switch only
   because all its reads happened to lie before it. Do not "harden" this
   the other way around by routing toolchain reads through the main-tree
   path: that same branch switch would have turned every main-tree read
   into ENOENT — the freeze is the robust answer. Missing files ⇒ derive
   defaults per the ground rules, present them in one short message, and
   freeze *those* as a note in the same directory so the run's basis is
   on record either way.

   **Access-binding preflight, same moment (E-0032):** this run is
   autonomous after intake, so the bite point for a missing
   `access.local.md` is **here** —
   [../shared/config-discovery.md](../shared/config-discovery.md)
   § *Access bindings*. If the run's path will consult a binding (a
   tracker ticket source, a push policy that pushes, browser
   verification) and the file is missing, end the intake with the
   module's canonical fix line instead of dying mid-run. An access-free
   path (file tickets, commit-only, no browser) proceeds normally.

   **Payload divergence check, same moment:** compare the toolchain the
   base branch carries (`git ls-tree -r <base> .claude/skills`) against
   the main tree's current state of those files. A deviation is not an
   error — an unmerged setup branch or honest local drift are normal —
   but the run must name which toolchain it builds with: report the
   divergence as a marked assumption in the run plan, one line
   (how many files differ, and which side is newer if the manifest
   says).
4. **Detect a resume.** A ticket whose plan already has ticked-off
   steps *and* whose branch exists (worktree or not) is a resumed run:
   you continue from the first unticked step on the existing branch
   instead of rebuilding — the run plan says so, names the step you'll
   start at, and lists what the Stand lines say already landed.
5. Present the run plan in a few lines: the detected shape (below),
   resume or fresh start, the repos in scope and the branch name they
   all get, approach, and — if the runtime will be needed — the slot
   you'll start (the `N` you claimed and the values it derives, per the
   parallel-run recipe), plus any assumptions. One confirmation, then the dev can leave.

**Bundle mode — the named form of a non-interactive intake.** When nobody
is there to answer this round (you were launched as another skill's
subagent, a scheduled or detached run, or the dev said "just build it"):
put the run plan **and** every open intake question into **one** block,
each question with your recommended answer, then proceed on those
recommendations and mark each as an assumption in the report. No waiting
for a reply that cannot come, and no silent decisions either — the block
is the record of what you assumed. Interactive runs keep the single
confirmation above.

## Isolation — every run stands alone

**This section is the toolchain's isolation contract**, and it is not a
project setting: isolation is always on. Every skill that checks out code
or brings the app up inherits these rules instead of restating them — the
review family through `mr-review/core.md`'s *Gather & workspace*, which
points here. Exactly two things vary, and neither is configuration: a run
**degrades** where isolation is provably impossible (point 1, and it says
so in one line), and a skill that can host itself as a background agent
may be told to stay in the dev's session instead (`mr-review`'s
`--attached`) — that is about *hosting* a run, never about isolating it.

Parallelism across tickets happens across **sessions**, not inside one
call: while you build this ticket, the dev may run `implement` for the
next one in another chat. You therefore isolate yourself, always:

1. **Own worktree, own branch — in every repo in scope.** Which repos are
   in scope comes from the plan or the ticket; a change spanning backend
   and frontend has two, and the isolation promise has to cover both or
   it covers nothing. Create the **same branch name** in each repo, each
   in its own worktree, at the layout `workflow.md`'s `## Isolation`
   block names — with the **branch slug** as the directory name: `/` →
   `-`, `#` dropped (`feature/#2085-x` → `feature-2085-x`; the block's
   dirname line carries the project's rule if it differs). A literal
   branch name in the path breaks tooling downstream — `/` nests
   directories, and a `#` broke Tailwind's `@config` resolution and the
   browser CLI's daemon paths in a real run. The same slug names the
   browser session (point 3) and every per-run resource derived from
   the branch:

   ```
   git worktree add tmp/worktrees/<branch-slug> -b <branch> <base>   # per repo (default)
   git worktree add <root>/tmp/slots/<branch-slug>/<repo> -b <branch> <base>
   ```

   The root-slot layout exists for workspaces whose repos reference each
   other by relative path: from a worktree inside one repo, `../<sibling>`
   still resolves — to the sibling's **main** working tree, so the run
   leaves its own isolation without any error to notice. No `## Isolation`
   block ⇒ use the per-repo layout and name it as an assumption.

   **A fresh worktree is not yet an equivalent tree.** Creating it is
   the easy half; before trusting any command in it, run the
   **worktree-needs checklist** per repo (the `## Isolation` block's
   worktree-needs line lists what setup found; no line ⇒ check
   yourself) — and say in the report what you copied or linked:

   1. **The toolchain is never copied into a worktree** — the one item on
      this list that is a *don't*. Committed, `.claude/` and the root
      instruction files travel with the checkout; where a project
      gitignores them, the run **reads them from the main tree** at
      `<main-tree>/.claude/…`, read-only, per `workflow.md`'s
      `## Isolation` → *Toolchain in a worktree*. Copying is not the
      convenient variant, it is a defect: a `.claude/skills/` under
      `tmp/` registers as **another skill scope** for every session
      rooted at the workspace, and that was observed in both directions
      between parallel runs — this run's copy in the neighbour's session
      and the neighbour's in this one. What a run needs is read access,
      which the main tree already gives it. Everything below is app and
      test state.
   2. **Gitignored local config the app and tests read** — `.env`,
      `.env.*` per repo. Copy or symlink them in; a worktree without
      them is a different machine, and the typical symptom is an
      app-wide test failure (whole API modules red) while the code is
      fine.
   3. **Dependencies for the new path** — a virtualenv living outside
      the repo is keyed to the project *path* (run `poetry install`
      again), `node_modules` is per-directory (`npm ci`, or symlink it
      to save minutes and disk; Claude Code's
      `worktree.symlinkDirectories` setting exists for exactly this).
   4. **Gitignored fixtures or data files** the suite reads.

   Baselines in `workflow.md` carry a `@maintree`/`@worktree` qualifier
   per [../shared/command-baselines.md](../shared/command-baselines.md).
   A baseline measured in the other kind of tree than the one you run
   in is context, not a gate: before diagnosing failures as
   regressions, re-check the checklist above — and in doubt, diff
   failure *identities* against a throwaway baseline worktree instead
   of trusting counts.

   Commit per repo. **The closing order is part of the contract**, because
   a worktree's path dies with it while its branch does not: finish the
   work, then — where the workflow's push policy allows it — push and open
   the MR **from the worktree, while it still exists**, and only then
   remove **every** worktree you created and `git worktree prune` each
   repo (a cross-repo run leaves N behind, not one, and a run that dies
   leaves all of them). What outlives teardown is the branch, its commits
   and the run directory (point 4) — never a path inside a removed
   worktree, and no report ever hands the dev one.

   **Where isolation cannot be had it degrades — it is never switched off
   in advance.** Two cases, both established at runtime: `workflow.md`'s
   `## Isolation` records `Tooling sees worktrees: no` (a container
   volume-mounting the main checkout, so nothing inside it ever sees your
   tree), or `git worktree add` fails. Then, and only then: work in the
   main checkout, note the branch you found it on and `git stash push -u`
   if it was dirty (restore both at the end, also on error), and **report
   in one line that isolation was unavailable and why**. That field
   configures nothing away — it lets a run degrade knowingly instead of
   discovering it halfway through, and the line in the report is what
   keeps "isolated" from being claimed for a run that wasn't.
2. **Own slot when the runtime is needed** (preflight, browser
   verification). The workflow file's **parallel-run recipe** says what a
   slot consists of — which services are duplicated and which are shared,
   the **base values** it parameterises, in which order to start them. A
   slot is a formula, not a supply: `N = 0` is the dev's own environment
   (the bases themselves), your run takes an `N ≥ 1` and derives every
   value from the recipe's table (port `base + N`, database/schema and
   compose project `name_N`). Nothing is measured or reserved per slot —
   `N = 7` costs exactly what `N = 2` costs.

   **Claim your `N` by finding it free, never by assuming it.** Take the
   lowest `N ≥ 1` that passes both checks: `mkdir tmp/slots/.slot-<N>`
   succeeds — a directory, because `mkdir` fails atomically when another
   run already holds that `N` — **and** every value the formula derives
   for it is actually free (probe each port, check the database name). A
   port that is busy without a claim behind it belongs to something else
   on this machine, typically the dev's own service: skip that `N`, never
   bind over it. The claim lives at the root of the layout the
   `## Isolation` block names (`<root>/tmp/slots/` for the root-slot
   layout, the primary repo otherwise), so parallel runs see each other's;
   write branch and date into it, so a stale one is recognizable.

   **Release it at teardown**, with the slot itself: stop what you
   started, drop the slot's database, remove the claim directory. A claim
   whose ports are free and whose worktree is gone is stale — take it over
   and say so in the report. And **record the slot facts (`N`, ports, DB
   name, start commands) in the ticket's plan** (or the report if the
   ticket isn't writable), so they don't evaporate with the session.

   The recipe also lists the scripts that stay pinned to the base
   values. **Anything you regenerate must run against your own slot**, not
   the base port — a client generated from the other session's service
   is valid output built from the wrong schema, and nothing downstream will
   flag it. Where the recipe names no parameterised form for such a script,
   run it against your slot by hand and say in the report which script that
   was.

   And one compose-specific trap, because slot commands run from the
   worktree root: **never a bare `docker compose` in a worktree.**
   Without `-p <compose-project>_N` the project name derives from the
   directory name, and the up quietly targets the **base** ports and
   volumes — a real run tried to bind the dev's own Postgres port that
   way. The recipe's start commands carry the `-p`; anything you
   improvise carries it too.

   First check whether you need a slot at all: an `## Isolation` block that
   records a self-isolating test suite (own throwaway database per run)
   means test runs cannot collide, and a run that never touches the browser
   then needs no slot at all. No recipe in the workflow file ⇒ use the
   project's default environment and say so in the report: runtime steps
   may collide with a parallel run — the risk is named, never silently
   taken.
3. **The browser belongs to the slot**, per
   [../shared/browser-discipline.md](../shared/browser-discipline.md).
   Every browser phase runs in a named session bound to this run
   (`-s=<branch-slug>`, point 1's slug), never the default session — a parallel session
   navigating a shared tab silently invalidates your verification, and
   yours theirs. Named sessions isolate, so the browser is not a scarce
   resource; only a **singleton** browser is (CDP attach, opt-in), and
   there that module's lock convention applies and the report names
   browser isolation as unavailable rather than implying it held.
   And **checkpoint browser artifacts**: every screenshot goes to disk
   the moment it is taken, with an explicit `--filename=` into the run
   directory (point 4) — the browser is the least robust link in the run,
   and a stalled session must not cost evidence already gathered. The
   CLI's own default target, `.playwright-cli/`, is aged out by the
   committed SessionEnd hook, so nothing a report links may stay there.
4. **Own scratch directory — outside every worktree.** The run directory
   is `tmp/<ticket>/` in the **main checkout** of the run's primary repo
   (the first repo in the plan's `## Repos in scope`; a single-repo run has
   only the one). Everything the run must keep lives there and nowhere
   else: every subagent handback, the review loop's
   `review-round-<N>.md`, `_context.md` and seeding scripts, and every
   artifact a report links (screenshots, traces). The reason is the
   teardown above: a file inside a worktree is an audit trail with a
   delete date, and "keep it until the end of the run" and "remove the
   worktree" cannot both hold anywhere else. Same rule for anything a
   report **links** — a link into a directory some later cleanup may empty
   is a link into nothing.

   **This location is skill mechanics, not a project fact.** No
   `workflow.md` line moves it — a slot-table row naming an artifact
   directory included: layer precedence (project beats generated beats
   vendored) governs project facts, and the audit trail's survival is
   not one. A generated line that puts run artifacts into a worktree or
   parameterises them per slot is a config bug to report, not a
   precedence to honor.

   This is the run's one deliberate write outside its worktrees, and it
   stays harmless: `tmp/` is gitignored where `beyonder-setup` ① ran
   (check, don't assume — `git check-ignore -q tmp` costs nothing, and an
   unignored `tmp/` means your run directory shows up in the dev's next
   `git status`; say so once in the report rather than adding the entry
   yourself) and the
   ticket namespaces the directory, so parallel runs never collide and
   nothing of the dev's is touched. **Teardown never touches it either,
   and neither does any hook** — the committed SessionEnd hook ages out
   the browser CLI's own scratch directory and nothing else
   ([../shared/browser-discipline.md](../shared/browser-discipline.md)
   § *Where artifacts go, and what may age*), which is precisely why a
   linked screenshot is written here with an explicit `--filename=`
   instead of being left where the tool dropped it.
   The report names the path, so the trail is findable once the worktrees
   are gone.

## Budget guard — look before every step, never die mid-edit

Two halves, so a usage limit never kills a run inside an edit: the
guard avoids starting what cannot finish, and the floor makes it cheap
when the guard misses.

**The guard (opt-in, fail open).** `workflow.md`'s `## Usage snapshot`
block names a snapshot file (default `~/.claude/usage-snapshot.json`)
that the dev's status line keeps current with
`{ts, context_pct, five_hour_pct}` — the five-hour limit is
account-wide, so one file serves every parallel session. Before
launching each unit of work (Single mode step group, Collection
theme, a review round), read it:

- **`five_hour_pct` above ~90 %** ⇒ start nothing new. Write the Stand
  and a **resume note** into the ticket (steps done, next step, branch,
  worktree paths, slot facts), commit everything, then **end the run
  and tell the dev the reason** — they decide whether to wait for the
  window or buy extra usage. Never idle-wait inside the session.
- **File missing, unparsable, or stale** (`ts` older than a few
  minutes) ⇒ proceed. The guard is opt-in and the snapshot payload is
  not a documented contract — it must never block a run. Known gap:
  the status line renders only in interactive sessions, so a machine
  running only detached sessions has a stale file and the guard falls
  open exactly where runs are unattended.

**After a budget stop, a returning child does not restart the run.** A
subagent launched before the stop can finish minutes later, and its task
notification arrives in a session that deliberately ended. Then, in this
order: read its handback file, append what it produced to the ticket's
Stand lines and the resume note (so nothing built is lost), commit that
bookkeeping — and **stop again**. The notification is a receipt, never a
work order: it does not open a new review round, launch the next step
group, or reopen the run, no matter what its child suggests as a next
step. If several arrive, log each the same way. The dev decides when the
run continues; only they can know whether the usage window reopened.
(General rule for the channel:
[../shared/subagent-handback.md](../shared/subagent-handback.md) §
*Late notifications*.)

**The floor (mandatory, guard or no guard).** Commit after every step;
tick the step off and write a one-line "Stand" into the ticket as it
lands; and honor the resume path: `implement` on a ticket whose plan
has ticked-off steps and whose branch exists **continues from the
first unticked step instead of rebuilding**. The guard is
probabilistic; the floor is what holds when it misses — an
interruption then costs one step, not the run.

## Phase 1 — Shape gate

- **Single concern** — one feature, bug, or refactoring, however large:
  → Single mode.
- **Collection** — a ticket that is really a list of many small,
  mostly independent issues (bug lists, design-polish ACs,
  "Kleinigkeiten"): → Collection mode.

## Single mode

1. **Branch** from the workflow's base branch, named per its
   convention — in its own worktree, per the Isolation rules.
2. **Plan & group.** With a plan in the ticket: take its task list and
   partition it into **step groups** — a handful of related steps that
   share a code area and form a natural commit boundary. Groups, not
   single steps (one subagent per step means one cold-start
   re-orientation in the worktree per step), and never the whole plan
   as one group. Without a plan: explore the affected code (patterns
   similar features follow, tests, conventions), derive the task list
   yourself, record it in the report — assumptions marked — then group
   the same way.
3. **Build in subagents, one per step group — the parent does not
   build.** A single agent that carries a long build ends up reasoning
   with a context full of step-3 file contents by step 15; the durable
   state lives in the ticket anyway. Launch the groups **sequentially**
   (they share the worktrees), each subagent handed exactly:

   - its steps, quoted from the plan, plus **only the watch-outs that
     touch them**;
   - the branch, the worktree path(s), and the project's stack skill;
   - the few file paths it will work in.

   - **its handback path**, `tmp/<ticket>/build-group-<n>.md`, per
     [../shared/subagent-handback.md](../shared/subagent-handback.md).

   The subagent builds task by task following the codebase's existing
   patterns, watch-outs binding, and **commits each task as it lands**
   (workflow format) — one big commit at the end is exactly the shape
   that loses work to an interruption. It **writes its result to the
   handback path** and returns the same content compactly: files
   touched, commit hashes, deviations from the plan, new watch-outs —
   never file contents. A missing handback file after a finished group is
   a failed group (module rule): relaunch it from its last landed commit,
   never reconstruct what it did from the notification.
   A subagent must not have to *re-derive*
   context: anything the next group needs is in the ticket or in a
   returned summary — exactly the discipline `technical-planning`
   already produces. If a step's outcome matters to a later group, the
   parent writes it into the ticket now, not into its own memory.

   Between groups the parent does bookkeeping only: tick the landed
   steps off in the ticket and append their one-line "Stand" entries
   (what landed, commit hash) — via the write path the ticket source
   names (with file-based tickets that is `Edit`, so it is simply
   available; with a tracker it needs write access) — write returned
   new watch-outs into the ticket, extend its commit log — then run
   the Budget guard and launch the next group. The parent's context holds plan, tick-offs, and
   commit log: a few kB per group. A group that comes back hot —
   large deviations, died mid-group — is split finer and relaunched
   from its last landed step (the commits and Stand lines say where
   that is), not retried whole.
4. **Test & QA.** Affected tests plus the workflow's QA gates
   (checks, lint, migrations — whatever it lists) as the closing
   step — run it as a subagent too when the output would be large.
   Fix until clean.
5. **Commit** whatever the QA fixes touched, per the workflow's format —
   the feature work is already committed step by step.

## Collection mode

The workdown approach — every point ends with an evidence-backed
verdict, nothing is silently skipped:

1. **Enumerate** every point of the ticket into a numbered list,
   preserving its grouping. Points that hide a product decision are not
   built — they get a verdict of **Unclear** with the concrete question,
   collected for the report (autonomy rule: no mid-run questions).
2. **Preflight**: your own slot runs (per the Isolation rules;
   environment facts from `.claude/beyonder/environment.md`, missing
   config ⇒ browser-verified points degrade to code-level verdicts,
   named in the report), test login works, and per point: can its state
   be produced with the local data? Seed what's missing (script kept in
   `tmp/<ticket>/`).
3. **Shared context file** `tmp/<ticket>/_context.md`: environment,
   code map, verified build/test commands, seeded data, conventions
   agents would otherwise violate, the verdict spec. Append every new
   trap an agent discovers. Design points get a Figma node map via the
   `figma` skill — record the map path it reports in `_context.md`.
4. **Sequential subagents**, one per theme (1–5 related points, grouped
   by code area; functional bugs before design polish), each prompted
   with: read `_context.md` first; the point quoted verbatim; repro
   steps and seeded records; root-cause hints; scope guards (what NOT
   to revert); its handback path `tmp/<ticket>/theme-<n>-<slug>.md` per
   [../shared/subagent-handback.md](../shared/subagent-handback.md); the
   step sequence replicate → before-screenshot → fix → after-screenshot →
   tests → verdict, verdicts written into the handback file. Strictly one
   at a time — they share the working tree.
5. **Verdicts** (non-negotiable taxonomy): **Fixed** (evidence: before/
   after, files, tests) · **Unable to replicate** (proof of looking,
   hypothesis) · **Unclear** (the question to ask) · **Needs Figma**
   (the missing frame). Then the combined test suite of the touched
   apps, and commits per the workflow.

## Phase 2 — Review loop

You do not hand over a branch with known problems in it. The review
runs, you fix, the review runs again — until a pass finds nothing new.
Severity decides the **order** of fixes, never whether they happen.

**Round 1.** Launch **`full-review` as a subagent** over the run's
worktrees — all of them, so a cross-repo change is reviewed as one change
rather than per repo (it degrades to `code-review` when no ACs could be
resolved); hand it your slot (URLs/ports) so it doesn't start a second
one, and the frozen config directory `tmp/<ticket>/config/` (Phase 0,
point 3), which it reads instead of the live `.claude/beyonder/`.

**The handback is a file, never a message** — the general rule from
[../shared/subagent-handback.md](../shared/subagent-handback.md), applied
here: hand the reviewer the report path
`tmp/<ticket>/review-round-<N>.md` in the run directory (Isolation, point
4) and read that file when the subagent finishes. The files stay until the
end of the run — they are the loop's audit trail, and the report's
round-by-round summary is written from them; that is exactly why the run
directory sits outside the worktrees the run removes. A finished
reviewer whose file is missing is a failed round: re-run it, don't
reconstruct findings from memory.

**Split each round's findings into two sets.** Everything that survived
the review's confidence filter is relevant by construction, so the split
is only about whether *you* can settle it:

- **Fix set** — truth established by reading the checked-out code (not
  inferred from the diff) **and** the correct behavior follows from the
  ticket, the plan, a documented convention, or an existing house
  pattern. Blocker or nitpick, it gets fixed. Secrets findings are
  always in this set.
- **Raise set** — everything else, each carrying the reason it wasn't
  fixed: **unverified** (plausible, but you could not establish it — no
  repro, unreachable runtime state) or **judgment** (real, but the fix
  is a product decision, an architecture trade-off, or a refactor beyond
  this ticket's scope). Never silently applied, never silently dropped.

**Then loop.** Fix the fix set, blockers first — for more than a
couple of findings, as a **fix subagent** per round, handed the same
way as a step group: the round's `review-round-<N>.md` path to read, its
own handback path `tmp/<ticket>/fix-round-<N>.md` to write, the fix
set, the worktree paths, the touching watch-outs; it returns files,
commit hashes, deviations. The parent stays bookkeeper here too.
Commit the fixes separately from the feature commits; re-run the
affected tests.
Re-review scoped to **the fix commits' diff plus the files they touch**
— callers and tests included, because a fix breaks things outside its
own hunks. The content half re-verifies only the ACs whose behavior the
fixes touched.

**Stopping** — three exits, and the report names which one applied:

1. A round produces no new fix-set findings (**new** = an identity not
   yet seen this run, per
   [../shared/review-passes.md](../shared/review-passes.md)). The normal
   exit.
2. **Round cap: 3 reviews.** Fix-set findings still open move to the
   raise set and the report says the cap was hit — a cap reached in
   silence would read as clean.
3. **Oscillation** — a round reintroduces a finding an earlier round
   already fixed. Stop and raise the finding together with the two
   conflicting fixes; that is a design question, not a bug.

## Deliverable

One report: **branch and commits per repo in scope** · what was built (or
the verdict table in Collection mode) · test/QA results as they are ·
**the review loop**:
how many rounds ran and which exit ended it, what each round fixed (one
line per finding), and the raise set with every item's reason
(`unverified` / `judgment`) · the AC table from the last `full-review` ·
slot facts if a parallel slot ran (also written into the ticket's plan) ·
the **run directory** path, so the audit trail is findable now that the
worktrees are gone · assumptions made · open items (Unclear verdicts, PO
questions) · **the one proposed learning**, if a review round produced one:
carried up from its handback unchanged, per
[../shared/review-passes.md](../shared/review-passes.md) § *Learnings
writeback*. You never write the learnings files — this run has nobody to
confirm a rule that would suppress future findings, so the proposal waits
in the report for the dev.

Close with the handover, and name only what still exists. Where the push
policy let you push, the MRs are already open (Isolation, point 1) and the
report links them — one per repo, in the order the plan's
`## Repos in scope` states, which is also where the reason for that order
is written; don't re-derive it here. Otherwise the handover names the
**branch** per repo (branches survive their worktrees, paths don't) and
the next step: push, open the MR per repo in that order, then `mr-review`
takes over, once per MR.
