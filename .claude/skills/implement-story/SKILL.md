---
name: implement-story
description: Implement a story end to end - resolve it from a GitHub issue link, issue number or plain text, check it out into its own worktree, plan it, write it, get the local CI gates green, run a resumable sharded code review that never blocks on a dying reviewer, fix what it finds, play the story in a real browser to confirm it works, then commit, push and open the PR. Standalone - does not depend on the beyonder-dev toolchain or its config files. Use when asked to implement an issue or story via this skill, or to resume an interrupted run.
---

# Implement a story

One story, from issue to open PR, with a code review that survives its own reviewers dying and a browser
that confirms the thing actually works. Self-contained: reads only this repo's own `AGENTS.md` and
`docs/ai/`, never `.claude/beyonder/*`.

## Usage

```
/implement-story <github issue url | issue number | free text describing the story>
/implement-story --resume [slug]           # pick an interrupted run back up
/implement-story <story> --no-worktree      # work in this checkout instead of a fresh worktree
/implement-story <story> --deadline=900    # review wall-clock budget in seconds (default 720)
/implement-story <story> --no-content-review # skip the browser phase
/implement-story <story> --content-port=9000 # port for the smoke server (default 8765)
/implement-story <story> --no-pr           # stop after pushing, do not open the PR
```

## The run directory

Everything durable lives in `.claude/runs/<slug>/` (gitignored) inside the story's own worktree. This
directory *is* the state - it is what makes a dead reviewer cost one lens instead of the whole run.

```
.claude/runs/
  .lock                this worktree's one-run-at-a-time lock: slug, branch, epoch seconds
.claude/runs/<slug>/
  spec.md              the story, resolved once, never re-fetched
  plan.md              the approved implementation plan
  state.json           phase, branch, shard status, attempt counts
  ci.md                latest gate results
  ci-logs/             full pre-commit and pytest output
  review/
    .started_at        epoch seconds, written when the round launches
    .head_sha          the commit the round is reviewing
    01-correctness.md  each shard writes its own file, incrementally
    02-django-data.md
    03-tests.md
    04-frontend.md
  findings.md          merged, deduped, triaged
  content/
    journey.md          the steps to play, written before clicking, with the result of each
    findings.md          what a player sees that is wrong
    smoke.sqlite3         the throwaway database the browser plays on
    server.log            the smoke server's output, where the tracebacks are
    .port  .pid            the running smoke server
```

A shard file ending in the line `<!-- shard-complete -->` is finished. A shard file **without** it is a
partial and is still used - its findings count, its coverage is reported as incomplete. No file at all
means that lens was never reviewed, which is reported as a gap rather than blocking the run.

`state.json` is what a later session resumes from, so its shape is fixed rather than improvised:

```json
{
  "slug": "faction-defeat",
  "issue": 21,
  "branch": "feature/faction-defeat",
  "base": "origin/main",
  "session": "faction-defeat [f69956]",
  "phase": "review",
  "deadline_seconds": 720,
  "ci_attempts": 2,
  "touches": ["apps/transaction/models/transaction.py", "apps/transaction/tests/models/test_transaction.py"],
  "review": {
    "head_sha": "c753616",
    "shards": {
      "01-correctness": { "status": "complete", "attempts": 1, "agent_id": "agent_x" },
      "02-django-data":  { "status": "running",  "attempts": 2, "agent_id": "agent_y" },
      "03-tests":       { "status": "gap",      "attempts": 2, "reason": "deadline" }
    }
  },
  "content": {
    "status": "pending",
    "port": 8765,
    "rounds": 0
  }
}
```

`base` is the ref every diff is taken against: `origin/main`, or a neighbour's branch when this story
stacks on one. `session` is what `ListAgents` calls this run - it tells each session its own name, and
writing it down here is what lets a neighbour address this one instead of guessing. `touches` is the file
list this run claims, which is how the neighbouring worktrees see it coming. `phase` is one of `spec`,
`plan`, `implement`, `ci`, `review`, `triage`, `content`, `ship`. A shard `status` is one of `running`,
`complete`, `partial`, `gap`. A `content.status` is one of `pending`, `pass`, `findings`, `blocked`,
`skipped`. Write the file after every phase transition and every shard state change - it is cheap, and it
is the only thing standing between an interrupted run and a restart.

## Before you start

Read `AGENTS.md` and `docs/ai/architecture.md`, `docs/ai/design.md`, `docs/ai/testing.md`,
`docs/ai/workflow.md`. They are normative for this project, in particular:

- **`ModelForm.save()` must only validate and persist.** No `transaction.atomic()` boundary, no
  `handle_message()`/side effects inside it - both belong in the view's `form_valid()`, called after the
  atomic block exits (see `AGENTS.md`, docs/ai/architecture.md § Forms vs Views, #333).
- Comments name constraints/invariants/whys the code cannot show, never narrative. No comments unless
  the why is non-obvious.
- Commit messages and code comments: English. Ticket/PR descriptions: German.

## Parallel runs

One story, one worktree - Phase 0 creates it. Nearly everything a run touches is per-checkout that way:
the branch, the run directory, the smoke sqlite database inside `content/`, and the port, which
`content-server.sh` probes upward from the default rather than assuming it is free. Two things still reach
across.

**The browser is shared across the whole machine.** If Playwright/Chrome MCP tools are backed by one
daemon, two content reviews can land in the same browser. Phase 6 asks the neighbours before the first
click.

**The neighbours are working the same repository.** Two stories editing the same files find that out at
the merge otherwise, so Phase 1 reads what the other worktrees have claimed and puts the overlap in front
of you at the approval stop. Django migration leaves are the sharp case: two branches both adding the next
number only collide once both land in one tree, so `migration-numbers.sh` checks names across siblings too.

**One run at a time per worktree.** Phase 2 rewrites the working tree, so a second run in the same
directory pulls the ground out from under the first. `.claude/runs/.lock` is one line -
`<slug> <branch> <epoch seconds>` - written in Phase 0 and deleted in Phase 7.

## Phase 0 - Resolve the story

**On `--resume`, find the run before anything else.** The run directory lives inside the story's own
worktree, so a resume started anywhere else sees no `spec.md` and would resolve the story a second time.
Walk `git worktree list --porcelain`, take the one whose `.claude/runs/<slug>/spec.md` exists,
`EnterWorktree` with its `path`, and skip the rest of this phase apart from the lock.

Derive `<slug>` as a short kebab-case name for the story (`faction-defeat`, `room-invite-links`).

- **Issue URL or number** - `gh issue view <n> --json number,title,body,labels,comments`. Write the title,
  body and any comment that changes the requirements into `spec.md`. Record the issue number in
  `state.json`; it becomes `Closes #<n>` in the PR.
- **Free text** - write it into `spec.md` verbatim, then add your reading of it underneath as
  "Interpretation". No issue number.

Resolve once. Later phases read `spec.md`, they do not re-fetch.

### Into its own worktree

```bash
git fetch origin
[ "$(git rev-parse --git-dir)" = "$(git rev-parse --git-common-dir)" ] || echo "already in a worktree"
```

Fetch first. The branch is cut from `origin/main`, never local `main`.

**Already in a worktree**, or `--no-worktree`: adopt the branch that is checked out and create nothing. A
worktree sitting on `main` still needs its own branch - `git switch -c <branch> origin/main`. If
`git status --porcelain` is not empty or a rebase/merge is in progress, stop and say so.

**In the main checkout**: create one.

```bash
git worktree add -b feature/<slug> .claude/worktrees/issue-<n>-<slug> origin/main
```

`feature/` for new behaviour, `fix/` for a defect, `chore/` for maintenance, matching this project's
Conventional Commits scope. The directory drops the `issue-<n>-` prefix when the story came in as free
text.

Then call `EnterWorktree` with `path` pointing at the new directory: the session moves in, and the rest of
the run happens there.

A fresh worktree carries no untracked files:

```bash
uv sync --all-extras --no-install-project
[ -d node_modules ] || yarn install
```

The worktree stays behind when the run ends. Phase 7 opens a PR, it does not merge one, and review
comments need a checkout to be answered in.

### Then take the worktree's lock, and say who you are

Record `base` as `origin/main` and `session` as the name `ListAgents` reports for this session.

```bash
mkdir -p .claude/runs
cat .claude/runs/.lock 2>/dev/null          # empty, or a slug that is not yours -> stop
echo "<slug> <branch> $(date +%s)" > .claude/runs/.lock
```

A lock naming a different slug means another run owns this working tree. Stop and say which one - do not
take it over. If that run was abandoned, its `state.json` says which phase it died in: resume it, or
delete the lock deliberately and say you did.

## Phase 1 - Plan, then stop

Write `plan.md`: the files you will touch, the models/views/forms/templates you will add or change, the
tests you will write, and anything in the story you consider out of scope. Record the file list as
`touches` in `state.json`.

### Neighbours

```bash
git worktree list --porcelain               # absolute paths - read them straight, do not cd
cat <other worktree>/.claude/runs/*/state.json
```

Skip your own worktree, and skip any run whose `phase` is `ship`. Intersect your `touches` with what is
left. Anything shared goes into `plan.md` under **Neighbours**, naming the neighbour's slug, branch and
phase. Match each neighbour's `session` against `ListAgents` to say whether it is still alive. Rows that no
`state.json` claims are other people's work; leave them alone.

If the call is to build on a neighbour's branch, record that branch as `base` in `state.json`. Only stack
on a branch the neighbour has already pushed.

**Present the plan and stop for approval.** This is the only mandatory stop in the run.

## Phase 2 - Implement

Work the plan. Tests are part of the story, not a follow-up - see `docs/ai/testing.md` before writing any
of them.

Keep commits in logical chunks as you go, Conventional Commits style (`feat: add split animation`,
`fix: correct room balance`), imperative, scoped to a single concern, no issue tag in the subject.

When the work is done, refresh `touches` from `git diff <base>...HEAD --name-only`.

## Phase 3 - CI gates

```bash
bash .claude/skills/implement-story/scripts/ci.sh .claude/runs/<slug>
```

Runs this project's actual gates: `pre-commit run --all-files` (twice, because ruff-format/djlint rewrite
files the first pass and only the second pass can confirm they're clean), `uv run coverage run -m pytest
&& uv run coverage report` (config in `pyproject.toml`; there is no `fail_under` gate here, so a drop is a
judgement call, not an automatic failure), plus `migration-numbers.sh` for the Django migration-leaf
conflict no CI run in a single worktree can see. Results land in `ci.md`, full output in `ci-logs/`.

Fix and re-run until pre-commit and pytest are green, counting rounds in `ci_attempts`. **The review does
not start on a red run.**

**After three red rounds, stop and report.** Three failures on the same gate means the plan was wrong, not
that the fix needs another attempt.

The formatting hooks rewrite files, so stage whatever they changed before the next commit.

## Phase 4 - Sharded code review

### Launch

1. **`git status --porcelain` must be empty.** Commit everything first. The shards review
   `git diff <base>...HEAD`, so uncommitted work is invisible to all of them.
2. `git diff <base>...HEAD --stat` - count changed lines and decide the shard count:

   | Changed lines | Shards |
   |---|---|
   | up to 200 | 1 |
   | up to 600 | 2 |
   | up to 1200 | 3 |
   | more | 4 |

   Take them in the order listed in [review lenses](references/review-lenses.md) - the lenses are ranked,
   so a small diff drops the least valuable ones and a deadline drops them too.
3. Write `review/.started_at` (`date +%s`) and `review/.head_sha` (`git rev-parse HEAD`).
4. Launch every shard **in a single message** so they run concurrently, one `Agent` call each with
   `subagent_type: "general-purpose"` and `model: "sonnet"`. Build each prompt from the template in
   [review lenses](references/review-lenses.md). Record the returned agent ids in `state.json`.

### Wait

Shard completions arrive as task notifications. On each one:

```bash
bash .claude/skills/implement-story/scripts/review-status.sh .claude/runs/<slug> <deadline_seconds>
```

Pass the deadline explicitly. Do not poll it on a timer - only look when a notification wakes you, or when
you have nothing else to do.

**Never re-read a shard's returned text as the source of truth.** The file is the deliverable.

### Retry, once

A shard is failed when its agent returns an error, or dies, or leaves no file. Retry it exactly once, with
the scope halved - hand the retry only the largest changed files by line count. Bump `attempts` in
`state.json`. A second failure is a gap, not a third attempt.

### Deadline

When elapsed exceeds the deadline (default 720s, `--deadline=N` to change it):

1. `TaskStop` any shard still running.
2. Anything with a partial file keeps its findings, marked incomplete.
3. Anything with no file is recorded in `findings.md` as
   `Not reviewed: <lens> - <reason>` and the run continues.

Continuing with a gap is the correct outcome, not a failure.

### Merge

Read every shard file that exists. Drop findings below confidence 80, drop exact duplicates and collapse
near-duplicates on the same file and line. Write the survivors to `findings.md`, most severe first, with
the not-reviewed gaps listed at the bottom.

Then call `ReportFindings` with the merged set.

## Phase 5 - Triage and fix

Fix everything that is a real defect in code this story touched. Do not fix pre-existing problems in
passing - note them in `findings.md` under "Out of scope, worth a follow-up".

Re-run `ci.sh`. **Do not re-run the review.** Instead, if the fixes were non-trivial, launch a single
`Agent` to check only `git diff <head_sha_from_review>..HEAD` for regressions the fixes introduced.

## Phase 6 - Content review

Everything so far checked the code against itself. This phase plays the story in a real browser and looks
at what a player would see. Skip it with `--no-content-review`.

Read [content review](references/content-review.md) first.

1. Start the app on its own throwaway sqlite database:

   ```bash
   bash .claude/skills/implement-story/scripts/content-server.sh fresh .claude/runs/<slug>
   ```

   `fresh` for the first round. Pass `--content-port=N` through as the third argument. Record
   `content.port` in `state.json`.
2. Write `content/journey.md` - the baseline journey plus the steps the story adds, each with its expected
   outcome - **before** you touch the browser.
3. Walk it with the browser tools, from this session, in one browser. **Do not fan this out to agents.**
   Ask sibling worktrees before the first click if a shared browser daemon is in play.
4. Record the result of every step in `journey.md` and every defect in `content/findings.md`. Check the
   network requests after each mutating click - a failed htmx call leaves the page looking fine.
5. Fix what the story broke, `content-server.sh restart`, and walk the failed steps again. **At most two
   fix rounds**, counted in `content.rounds`.
6. Re-run `ci.sh`. A content fix that reddens the suite is worse than the bug it fixed.
7. Stop the server, pass or fail:

   ```bash
   bash .claude/skills/implement-story/scripts/content-server.sh stop .claude/runs/<slug>
   ```

If the browser tools are not connected, or the server cannot be brought up, set `content.status` to
`skipped` or `blocked` with the reason and carry on to Phase 7. Never report a pass you did not see.

## Phase 7 - Ship

Commit the fixes, push with `git push -u origin <branch>`, and open the PR:

```bash
gh pr create --base ${base#origin/} --title "<title per docs/ai/workflow.md PR title pattern>" --body-file <body>
```

Title follows `docs/ai/workflow.md`: `#<issue-number>: <Short description>` when there's a linked issue,
else `<Short description>` - sentence case, no conventional-commit prefix.

The body carries: what the story asked for, what you built, `Closes #<n>` when there is an issue, the CI
result, a **Review coverage** line naming any lens that was skipped or partial, and a **Content review**
line saying which journey was walked in the browser and what it showed - or that the phase was skipped,
and why. Unless `--no-pr`.

Release the worktree's lock once the PR is open - `rm -f .claude/runs/.lock`. The worktree itself stays.

End with a short report: what shipped, what CI said, what the review found and what you fixed, what the
browser confirmed or broke, what was skipped and why, the out-of-scope list, and the worktree path and
branch.

## Resuming

`state.json` carries `phase`. On `--resume`, read it and re-enter at that phase. Within Phase 4, relaunch
only the shards whose status is not `complete`, and only if `review/.head_sha` still matches `HEAD`.

Within Phase 6, `content-server.sh start` reuses a smoke server that is still answering and reruns nothing
otherwise. Use `fresh` instead if the recorded results no longer describe the code.

If a run is interrupted anywhere, the run directory is enough to continue. Never restart from Phase 0 when
`spec.md` already exists.

## Cost rules

- Review the diff against `base`, never the repository.
- The neighbour scan is a file read, not a broadcast.
- Never re-run a shard that produced a complete file.
- Never re-review after fixes; check the fix delta instead.
- Never spend review wall-clock on anything ruff/djlint or the pytest run already catches.
- One retry per shard, at half scope. Then it is a gap.
- One browser, driven from this session, never fanned out.
- Walk the journey you wrote, plus at most ten exploratory clicks.
- Two content fix rounds, then stop. Always stop the server.
