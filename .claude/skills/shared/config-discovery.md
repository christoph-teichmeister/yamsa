# Shared module — finding the project config

Not a skill entry. This module answers three questions the same way for
every skill: **where are `workflow.md` and `environment.md`?** — once two
sources have been found and they disagree, **which one wins?** — and
**which access path did this dev bind their tools to?**

The files live in `.claude/beyonder/`. The complication is real projects:
consumers run **per repo**, while a multi-repo workspace often keeps one
`environment.md` at the **workspace root** — which is not a repo at all.
Without a defined rule each run invents its own, and the 0.4.0 eval had to
patch around it with pointer lines in three `workflow.md` files.

## The search path (first hit wins, per file)

Search for `.claude/beyonder/<file>` in this order:

1. **`$CLAUDE_PROJECT_DIR`** if the harness set it — the session's project
   directory is the most explicit statement of where the dev is working.
2. **Upward from the current working directory**, one level at a time:
   `./`, `../`, `../../`, … up to and including the **git repo root**.
3. **Two levels above the repo root**, for the multi-repo case where the
   workspace root holds the shared config and is not itself a repo. Stop
   there — never walk to `/` or into `~`.

Resolve each file independently: a repo may carry its own `workflow.md`
(commands are per repo) while `environment.md` comes from the workspace
root (the app is one app). That combination is normal, not a conflict.

**Worktrees, depending on one fact you can check.** *If* `.claude/` is
committed — the common case — a worktree carries the config with it, step 2
finds it, and nothing special is needed. *If it is not*, step 2 finds
nothing inside the worktree: read the config **read-only from the main
tree** at `<main-tree>/.claude/…`
(`dirname "$(git rev-parse --path-format=absolute --git-common-dir)"`) and
never copy it in. One call decides which case you are in
(`git ls-files .claude | head -1`), and the project's own answer —
`workflow.md`'s `## Isolation` → *Toolchain in a worktree* — beats this
paragraph where the two differ. Gitignored parts (`reviews/`, local
settings) live in the main tree in either case: read those read-only from
there, never write them from inside a worktree.

**Multi-repo cross-check.** When the same file exists both in the repo and
at the workspace root, the repo's wins (step 2 before step 3) — and say so
in one line where it matters, because a stale repo-local copy shadowing the
maintained root one is otherwise invisible.

## Layer precedence — project beats generated beats vendored

Three team layers instruct a run — plus one personal layer above them
(next paragraph). Two of them will eventually contradict each other while
**both look verified**. The one closer to the team's own hand wins:

1. **What the team wrote by hand** — the repo's root `CLAUDE.md` and
   `AGENTS.md`, contribution docs, a rule the project marked as hard.
2. **The generated layer** — `.claude/beyonder/*`, written by
   `beyonder-setup` and measured against *this* project in its step ④.
3. **This vendored payload** — the skills and shared modules, written by
   people who never saw this project.

**The fourth layer sits above all three (E-0032):
`.claude/beyonder/access.local.md`** — per dev and per machine,
gitignored, written and migrated **only** by `beyonder-setup`. It is
resolved on the same search path as its siblings; being gitignored, in a
worktree it is read read-only from the main tree like every gitignored
`.claude/` part. It carries two kinds of content:

- **`## Access` bindings** — this dev's chosen way to each access path
  (host CLI vs. MCP, browser tool, Figma, ticket-source auth), each line
  with its last measured state and date. The contract for consuming them
  is the *Access bindings* section below.
- **Fact overrides** — a team fact shadowed under the **exact** team
  heading and field name. Lookup is trivial: local first, then team.

**Visible override, always.** Every run that honors a local override
names it in its output — "Base branch: `develop` — overridden by
`access.local.md`; team config says `main`". Drift is allowed; drift in
silence is not: the file is unversioned, no reviewer ever sees it, and
this rule is its entire safety story. The skill-mechanics exemption
(run directory, audit-trail location) binds this layer exactly as it
binds the project layer: no `access.local.md` line relocates skill
mechanics either.

Not a ranking of importance but of knowledge: 3 states what holds for most
projects, 2 what was measured in this one, 1 what the team decided anyway.
So a vendored imperative is the **default that holds until a higher layer
speaks** — where no higher layer says anything, it is the rule and not a
suggestion. Where one does, you follow the higher layer and **name the
deviation in one line** in the report, with both sources. You never resolve
it the other way, and you never stop mid-run to ask which of the two to
obey: the precedence *is* the answer. (`beyonder-setup` ③ does ask in one
narrow case — not which layer wins, but which capability to give up when it
cannot generate a compliant value at all.)

Two limits worth stating, because they are where this gets misread:

- **Silence is not permission.** A higher layer that says nothing about
  your case has not overridden anything. Deferent wording in layers 2 and
  3 exists for the collision, not as a general escape hatch.
- **A rule marked hard is not negotiable by a generated file.** Where a
  generated recipe and a hard project rule cannot both be satisfied — the
  eval's case: a slot database on the port the root `CLAUDE.md` fences off
  — the rule holds. Route around it (another port, an own container, your
  own schema) or **degrade that capability and report both sources**;
  a hard rule is a boundary, not an ambiguity to resolve, and it is never
  the thing that gets bent. `beyonder-setup` ③ is not supposed to write
  such a value at all (its *Generate* sub-step) — where it does anyway, the
  reader is the last line of defence.

This settles conflicts **between files**. Who may write which file is a
separate rule and unchanged: one writer per file, `beyonder-setup` for the
generated layer and for `access.local.md`.

## Access bindings — the `## Access` section of `access.local.md`

The contract every access-consuming skill follows (`glab` for the host,
`browser-discipline.md` for the browser and Figma, preflights in
`implement` and the mr-review family). Four rules:

1. **The binding is strict.** A line like `gitlab: mcp` means the run uses
   the MCP and only the MCP. When the bound way fails, degrade as usual —
   one sentence plus paste-ready content — and **never silently switch to
   the tool the dev did not choose**. There is no preference cascade any
   more: "CLI preferred, MCP fallback" survives only as the default
   binding `beyonder-setup` proposes.
2. **Missing file = hard requirement, enforced at the bite point.** The
   first step that would consult a binding — a host call, a browser start,
   a Figma read — refuses with the canonical fix line:
   > No personal access setup — run `/beyonder-dev:beyonder-setup`
   > (the personal part takes ~2 minutes).
   Access-free paths (a local diff report, a code-only review) run
   normally. A **detached or autonomous run** checks at its preflight —
   before any checkout — whether its path will consult a binding, and
   refuses there instead of dying mid-run.
3. **The measurement is advisory honesty, never a gate.** Each binding
   line carries the last measured state with its date (`glab ✅
   28.08.2026, MCP ✅ read-only`). Skills follow the binding regardless of
   the date — a failing call at runtime is the real freshness test and
   takes rule 1's degrade path; an old date only makes the message smarter
   ("measured 3 months ago — re-run `beyonder-setup`"). No TTL, and no
   consumer ever re-measures or rewrites the file (that would be an
   unversioned write mid-run, E-0031).
4. **Schema evolution is the setup's job.** The file carries a
   `schema:` line (`v1` today). Consumers tolerate older schemas where
   they can; where they cannot, the message says "re-run
   `/beyonder-dev:beyonder-setup`". Only the setup migrates the file
   (diff + consent); `beyonder-update` never touches it.

## When nothing is found

Not a failure of the run: degrade exactly the capability that needed the
file, name the file and `beyonder-setup` as its maintainer in the summary,
and continue. Never ask the user mid-run for a value the file would have
carried, and never invent one.

## For the writer

`beyonder-setup` records, in each repo's `workflow.md`, **where the config
it did not write locally lives** — one line, so a human reading a single
repo sees the layout too. That pointer is a courtesy for humans; consumers
rely on the search path above, not on the pointer.

Where the generated layer knowingly overrides a vendored default, it says so
**at the value**, naming what it overrides — the 0.5.0 eval's one working
example is a `workflow.md` line that corrected this module's own worktree
claim by name, and the run that read it needed nobody to explain the
precedence. An override recorded that way costs one clause and saves the
next reader the conflict.
