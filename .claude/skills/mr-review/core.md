# Shared core — ground rules, preflight, workspace, cleanup

This module is the **MR/PR wrapping**: how a run finds its MR, reads the
project config, gets a workspace, and settles its debts. What gets
reviewed or verified lives in the shared modules
([review-passes.md](../shared/review-passes.md) for code,
[content-checks.md](../shared/content-checks.md) for the running app)
and in [walkthrough.md](walkthrough.md) for documentation.

Two entry skills use it; each declares its **mode**:

- **review** — `/mr-review`, the full review pipeline
- **walkthrough** — `/walkthrough`, standalone feature documentation. Its
  object is one of three (branch / ticket / MR) — without an MR there is no
  IID to resolve and nothing to check out; the steps below say what that
  removes.

`/content-review` uses this module **only on its MR path**, and only for
the review-mode Preflight, Gather & workspace and Cleanup steps — it is
not a walkthrough and derives nothing from one; its checks come from
`content-checks.md`.

Steps below are tagged with the modes they apply to; an untagged step
applies to all modes.

## Ground rules (all modes)

**Golden rule: never ask the user anything during the run.** (Permission
prompts for non-allowlisted commands — platform writes, scratch-DB drop,
git stash/checkout — are expected and don't violate this.) Missing
capabilities degrade gracefully and are listed in the summary.
**Deliverable exception:** a standalone skill's core deliverable — the
walkthrough in walkthrough mode — can never be "degraded away". If it is
impossible (browser tool missing, environment dead), stop and report
exactly why instead of delivering an empty shell.

"**The summary**" in this module means the run's final output, whatever
the mode produces: the review summary note or report (review), the
walkthrough note, ticket comment or report (walkthrough).

All user-facing output is written in the configured language; the message
wording in these files is canonical English — render it in that language.

**The setup nag (canonical form).** Wherever this family degrades a
capability over missing, broken or stale config, the summary line is
`<what is missing or broken> — run /beyonder-dev:beyonder-setup step 3`
— with `step 3 review` when the entry lives in `review.md`, `step 3
parallel` for the parallel-run recipe, and `step 4` for unmeasured
baselines. Files in this family say "setup nag" and mean exactly this
form; nobody restates it.

**Output sink:** the config's **Output** section names it. **remote** =
post to the MR/PR; only operational failures are reported in the
terminal. **local** = post nothing; write a markdown report under
`.claude/beyonder/reviews/` (each entry skill names its file) and keep
its artifacts in cleanup. [walkthrough] The sink is the ceiling, not the
choice: `local` here forbids posting, `remote` allows the destination the
invocation's `--to` names.

**Platform docs:** API mechanics (positioned discussions, suggestion
blocks, screenshot uploads, notes) are documented per platform — read the
one the config's Platform names before posting anything:
[gitlab.md](gitlab.md) (`glab`) or [github.md](github.md) (`gh`).
Everywhere these files say MR/`glab`, use the platform equivalent.
GitHub caveat: no image upload API — screenshot walkthroughs always go
into a local report there.

## Token discipline (binding in every mode)

Large MRs must not multiply cost across subagents. Four standing rules:

- **The diff lives on disk, not in prompts.** The Gather steps split it
  into per-file patch files under `<scratchpad>/mr-<iid>-diff/` plus a
  `manifest.md`. Subagents receive the manifest and the patch-directory
  path and read only the files their task covers. Never paste the full
  diff into any prompt — yours or a subagent's.
- **You (the orchestrator) never read the full diff.** Work from the
  diffstat and manifest; read individual patch files only to verify a
  specific finding or resolve a concrete disagreement between subagents.
- **Model routing.** Think in three capability tiers; instructions
  reference the tiers, and the table below is the ONLY place concrete
  model names appear — when names change or the skill is ported to
  another harness, update only this table.

  | Tier | Work | On Claude Code (Agent tool `model` param) |
  |---|---|---|
  | **judgment** | bug passes, requirements pass, finding filtering | inherit the session model (omit the param) |
  | **checklist** | backend/frontend/convention passes | `sonnet` |
  | **mechanical** | change listing, description draft, thread indexing, coverage-gap sweeps | `haiku` |

  Never route a bug-finding task below the judgment tier — recall is
  the product.
- **Compact returns.** Subagents return only the structured form their
  caller defines — for findings: bodies ≤ 80 words, no narrative report
  around them.
- **Handback through files.** Where a subagent's result is more than a
  handful of findings — a pass's full output, a coverage manifest, a
  narrowed re-check — name its handback path in the briefing
  (`<scratchpad>/mr-<iid>-handback/<phase>-<id>.md`) and read the file
  when the task notification arrives, per
  [../shared/subagent-handback.md](../shared/subagent-handback.md).
  Messaging is best effort; a run resumed after a limit is no longer
  addressable for its running children. Delete the directory in Cleanup
  with the diff directory.

## Preflight

1. Resolve the MR IID from the argument (number, `!123`, or URL). Strip
   invocation flags first — a flag says how the run is hosted or where its
   output goes, never what it reviews, and a flag parsed as an object is a
   run against the wrong thing.
   [walkthrough] Only for an MR object; a branch or ticket object has no
   IID, and its run tag stands in wherever these steps say `mr-<iid>`.
2. Read project config: `.claude/beyonder/review.md`. Locate it and its
   siblings (`workflow.md`, `environment.md`, `stack.md`) per
   [../shared/config-discovery.md](../shared/config-discovery.md) — in a
   multi-repo workspace `environment.md` may live a level above the repo.
   Where two of these sources contradict each other, or one of them
   contradicts the repo's root `CLAUDE.md`, that module's § *Layer
   precedence — project beats generated beats vendored* decides it; the
   run follows the higher layer and names the deviation in the summary
   instead of asking. Missing file ⇒ continue with defaults (local-only,
   no walkthrough, threshold 80, nitpick cap 3) plus the setup nag
   (`step 3 review`). In walkthrough mode a missing config is a hard stop
   (no environment, no credentials — the deliverable is impossible; say
   so).

   **Soft schema validation** (never block a run over config
   formalities): the config should declare `schema: v5` and contain the
   nine v5 sections (Project, Output, Comments, Ticket, Prerequisites,
   Credentials, Flows, Project specifics, Review behavior). For every
   section that is missing or unreadable, degrade exactly that
   capability, use defaults where they exist, and add one setup nag
   naming the broken part (`step 3 review`). Fields set to `-` are
   deliberate opt-outs, not gaps — skip silently. An older schema marker
   (`schema: v4`) or a legacy `.claude/mr-review/` directory is a
   pre-0.7.0 setup: this validation carries it as far as its sections
   still match, ignored fields are ignored rather than honored, and the
   nag names the migration (`step 3 review` migrates both).

   **Personal access layer (E-0032):** read
   `.claude/beyonder/access.local.md` with the config. The bite point is
   here, before any checkout: an MR/PR object, a remote sink, or a
   tracker ticket source needs the **host** binding; the content half and
   the walkthrough need the **browser** binding; the design axis the
   **figma** binding. Any of those ahead and no file ⇒ refuse now with
   the canonical fix line
   ([../shared/config-discovery.md](../shared/config-discovery.md)
   § *Access bindings*); an access-free run (local sink, branch object,
   code half only) proceeds. Bindings are strict — the bound tool, never
   the other one.

   Commands (validate/build, tests incl. targeted variant, lint,
   migrations) are read from `.claude/beyonder/workflow.md`;
   walkthrough-environment facts (server setup/serve/teardown, base
   URL, data policy, browser tool) from
   `.claude/beyonder/environment.md`. A missing file or entry degrades
   exactly like a missing config section — same soft-degradation
   semantics, same setup nag.

   **Command baselines** ([../shared/command-baselines.md](../shared/command-baselines.md)): each command
   carries a `baseline:` recording what it reports at its measured base
   state (base branch + setup commit; the module has the details).
   Honor it — this decides whether a failure is the MR's fault:
   - `clean` ⇒ **gate**. A failure was introduced by this diff; report it
     as a blocking finding.
   - `dirty:N` ⇒ **advisory**. The command already fails on the base
     branch, so the team does not enforce it. Run it scoped to the
     changed files and report **only what the diff introduces** — never
     the pre-existing N, never a raw "validation failed". If nothing new
     appears, the slot is silent.
   - `unavailable` / `-` ⇒ don't run it; apply the recorded `heuristic:`
     if one is configured.
   - **missing** `baseline:` ⇒ treat as `dirty:unknown`: advisory, scoped
     to the diff, plus the setup nag ("commands unmeasured", `step 4`).
     Never promote an unmeasured command to a gate.
   - A baseline older than 90 days is stale: still usable, but say so in
     the summary. Never block on it.

   The rule behind all of this: **if merged code fails a tool, that tool
   is not enforced — this review does not adjudicate it.**

   **Prerequisites** (table) [review, walkthrough]: run each entry's
   check command. `review`-owned services are yours to start and stop —
   don't expect them up. For a `user`-owned service that is down: run its
   fallback command if configured (and re-check); otherwise apply the
   named consequence — abort, or skip the named capability and record it
   for the summary (deliverable exception applies).

   **Stale-config rule** (applies to every later step): when a
   *configured fact* fails in practice — login rejected, server won't
   bind the configured port, a check/fallback/teardown command errors, a
   flow's start URL 404s — treat it like a missing section: degrade that
   capability, finish the run, and name the exact config entry in a setup
   nag ("Config entry broken (<entry>)").
   Never burn the run retrying a config value that reality contradicts.
   (Deliverable exception: in walkthrough mode a stale entry that kills
   the walkthrough itself ⇒ stop and report it, don't "degrade".)
3. [review; walkthrough uses only its layer definitions] Read the stack
   checks file `.claude/beyonder/stack.md`. Missing ⇒ run only the
   generic passes and nag in the summary like a missing section.
4. [review] Read learnings, both layers if present:
   - Project: `.claude/beyonder/learnings.md`
   - General: `~/.claude/beyonder/learnings.md`
   Learnings are binding review guidance: they suppress finding types the
   team has rejected and add checks the team has requested.
5. Resolve posting identity (remote mode only): the invoker's `glab`/`gh`
   auth, with the marker footer (see platform doc) on every note.
   Exception: if `REVIEW_BOT_TOKEN` is exported, prefix posting calls with
   `GITLAB_TOKEN=$REVIEW_BOT_TOKEN` (GitHub: `GH_TOKEN`) and the footer is
   only required on the summary.
6. [review, walkthrough] Verify the configured browser tool
   (`.claude/beyonder/environment.md` → `Browser tool:`, with its
   `Install:` line — the field belongs to `beyonder-setup`, which always
   writes it, so a missing binary reads as a fix instruction, not a
   mystery).
   Unavailable ⇒ review: the content half and the walkthrough both fall
   away (both are observed in the app), the code half runs alone and the
   summary names the missing tool **with its install command**;
   walkthrough mode: hard stop.
7. Fetch the ticket per the config's **Ticket** section: `branch-id` ⇒
   extract the issue ID from the MR branch name using the configured
   pattern and fetch it via `glab issue view`/`gh issue view`;
   `repo:<path>` ⇒ read it from the branch; `custom` ⇒ as described; `-` ⇒
   work in isolation. Extract the user story + acceptance criteria (ACs):
   they feed the requirements pass, the walkthrough and the "why" of the
   description (review) and the flow selection (walkthrough).
   Ticket not found ⇒ degrade to isolated run, note it in the summary
   (walkthrough mode with a **ticket** object: the ticket *is* the object —
   not found ⇒ stop, there is nothing to walk).

## Gather & workspace

1. Fetch MR metadata (incl. the target branch and — review mode — what
   positioned discussions need later; see platform doc). Do NOT fetch the
   full diff into context — the diffstat and the patch files from step 5
   replace it.
2. [review] Remote mode: fetch **all** existing discussions/threads
   (paginate!). Build two indexes:
   - Topics already discussed (by humans or by you) → never open a
     duplicate thread on these.
   - Your own unresolved threads (marker footer or own author) →
     candidates for resolution when posting.
   On busy MRs (more than ~30 threads), delegate the index-building to a
   mechanical-tier subagent that returns both indexes in compact form.
3. [review, walkthrough] Check out the MR branch. **Not a configured
   choice** — `review.md` carries no checkout strategy. Whether a run gets
   its own tree, and what it owes when it cannot, is the isolation
   contract's business:
   [../implement/SKILL.md](../implement/SKILL.md) § *Isolation — every run
   stands alone*, inherited here, degradation rule included. What is
   MR-specific is only the mechanics:
   - **worktree** (the way): never touch the dev's tree.
     ```
     git fetch origin refs/merge-requests/<iid>/head
     git worktree add <scratchpad>/mr-<iid> FETCH_HEAD
     ```
     (GitHub: `refs/pull/<pr>/head`. The fetched remote must be the one
     hosting the MR/PR — on fork/mirror setups substitute it for
     `origin`.)
   - **in-place** (the fallback, never a preference): checking someone
     else's branch out into the dev's own tree adds one duty the contract
     cannot know about — record the current branch; `git stash push -u` if
     the tree is dirty (remember whether you stashed!); fetch + check out
     the MR branch. Restoring the original branch and popping the stash in
     Cleanup is MANDATORY — also on error or abort.

   All commands from here (tests, server, lint) run inside that review
   workspace (the worktree, or the main checkout for in-place).

   [walkthrough] Only an MR object is checked out. A branch or ticket
   object is walked **where it already is**: no fetch, no stash, no
   checkout — its diff comes from the entry skill's Intake, and the working
   tree is only read and browsed.
4. [review, walkthrough — worktree checkout only] **Bootstrap the
   worktree before any command runs in it.** A fresh worktree is not yet
   an equivalent tree. Read `## Isolation` in
   `.claude/beyonder/workflow.md` and settle its `Worktree needs:` line:
   copy the gitignored config it lists (`.env`, …), install dependencies
   for the new path (or the symlink variant the line names), copy
   gitignored fixtures. `none found` ⇒ done in one line. No `workflow.md`
   ⇒ note "worktree unbootstrapped" for the summary and let the baseline
   rules carry it (an unmeasured command is never a gate). This restates
   the isolation contract's checklist (implement § *Isolation*) at the
   one step this module owes it — validation in a never-bootstrapped
   worktree produces app-wide false-red failures that look like the MR's
   fault. In-place checkouts skip this step: the dev's tree is already
   equivalent.
5. **Diff preprocessing** (deterministic; in the review workspace, or in
   the dev's tree for a walkthrough without checkout):
   ```
   git fetch origin <target>          # the checkout only fetched the MR head
   base=$(git merge-base HEAD origin/<target>)
   git diff --stat $base                          # your working view
   git diff $base -- <file> > <patch-dir>/<slug>.patch   # one per file
   ```
   Write the patches to `<scratchpad>/mr-<iid>-diff/`, then a
   `manifest.md` next to them: the diffstat, and per file its layer
   (backend / frontend / config-infra, by the stack file's layer
   definitions) and flags. Flag and handle:
   - **Noise** — lockfiles, generated/vendored/minified code, snapshot
     files, binary assets: no patch file, excluded from all review
     passes, one collective line in the change listing.
   - **Formatting-only** — `git diff -w $base -- <file>` is empty:
     excluded from review passes, listed as such.
   - **Sensitive** — per the default categories in
     [../shared/review-passes.md](../shared/review-passes.md) (tier
     gate), plus anything the stack file marks critical: forces the
     full tier (step 6).
   The manifest routes the review passes and feeds the drafting subagent
   (review), and decides which flows are affected (review, walkthrough).
6. [review] **Tier gate** per
   [../shared/review-passes.md](../shared/review-passes.md): after
   noise stripping, trivial vs. full. Record the tier and its reason
   for the summary.

## Cleanup (mandatory, even after errors)

Settle exactly the debts your mode incurred:

- Checkout [review, walkthrough]: remove the worktree
  (`git worktree remove`), or for in-place restore the original branch
  and pop the stash if one was created.
- App environment [review, walkthrough]: run the `teardown`
  steps from `.claude/beyonder/environment.md` if its `setup` ran (stop
  what you started, drop any
  scratch DB); a failing teardown step is a stale-config nag, but still
  tear down as much as possible by hand. In review mode this debt is
  incurred by the content half as well as the walkthrough — whichever
  brought the app up owes it, and it is settled once.
- Artifacts [review, walkthrough]: everything the content half and the
  walkthrough captured (`<scratchpad>/mr-<iid>-artifacts/`). If it went
  into a local report (local mode or GitHub), move the screenshots next
  to the report under `.claude/beyonder/reviews/` and keep them;
  otherwise (uploaded to GitLab) delete the directory. Never delete
  artifacts that no report or note references — that would discard the
  only evidence a verdict had. The counterpart of that rule is where the
  artifact was written in the first place: everything a report links was
  captured with an explicit `--filename=` into the artifact directory
  above, never left in the browser CLI's own `.playwright-cli/` — that one
  is aged out by the committed SessionEnd hook, so a report linking into it
  links into nothing
  ([../shared/browser-discipline.md](../shared/browser-discipline.md)
  § *Where artifacts go, and what may age*).
- Always delete `<scratchpad>/mr-<iid>-diff/` and
  `<scratchpad>/mr-<iid>-handback/`, and remove stray tool
  output directories the run created inside the project working directory
  if they didn't exist before the run. **Two directories are exempt
  because they are not yours:** `.playwright-cli/` (the browser CLI's own
  scratch — the committed SessionEnd hook ages it out) and `.playwright/`
  (the CLI's config), per
  [../shared/browser-discipline.md](../shared/browser-discipline.md)
  § *Ownership*. Deleting either would take the CLI's configuration or a
  parallel run's snapshots with it.
- Then print a one-paragraph terminal recap — with a link to the MR/PR,
  or the report path in local mode.
