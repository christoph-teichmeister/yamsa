# Shared module — browser discipline

Not a skill entry. This module is the toolchain's **own** rules for driving
the browser: which session a run uses, how it behaves on a browser it
cannot isolate, where its artifacts land, and what it must never touch.
Read it by path (`../shared/browser-discipline.md`) — it carries no
description of its own and is never loaded for you.

**What the CLI knows is not in here.** Commands, flags, snapshots, refs,
tracing, storage state, spec-driven test authoring (plan → generate →
heal) — all of that is the `playwright-cli` skill's own documentation,
installed by the CLI itself at `.claude/skills/playwright-cli/` (with
`references/` beside it). Consult it there. This file holds only what a
Beyonder run has to add, because the CLI cannot know it.

## Ownership — the CLI owns its own files

`playwright-cli` installs and maintains its skill documentation and its
workspace. Three paths therefore belong to it, and **no Beyonder skill,
template or hook writes, deletes or ages anything in them** (E-0026):

| Path | What it is | Who writes it |
|---|---|---|
| `.claude/skills/playwright-cli/` | the CLI's skill docs (`SKILL.md` + `references/`) | `playwright-cli install --skills` |
| `.playwright/` | the CLI's workspace config (`cli.config.json`) | the CLI, and the team by hand |
| the binary | `@playwright/cli`, global npm install | the dev |

The rule is the rule, not the three names: **what the CLI manages, we do
not touch** — a fourth path the CLI starts using tomorrow is covered by
the same sentence, and picking the rule off a list of names is how the
next one arrives unprotected. This is also why the toolchain no longer
vendors a copy of that skill: the CLI rewrites `SKILL.md` on every
`install --skills`, byte for byte, and warns on **every** invocation while
a modified copy is in place ("The playwright-cli skill at
'.claude/skills/playwright-cli' does not match the tool version").

`beyonder-setup` ② installs it, `beyonder-update` refreshes it on every
run. Missing binary — the fix line every skill quotes verbatim:

```bash
npm install -g @playwright/cli@latest    # provides the playwright-cli binary
```

## The personal binding — which tool, on this machine

`environment.md`'s `Browser tool:` field says what the **project**
verifies with (`playwright` or `-`); the dev's
`.claude/beyonder/access.local.md` carries the personal half — the
`browser:` line under `## Access`, with the last measured state of
`playwright-cli` on this machine. Consult it per
[config-discovery.md](config-discovery.md) § *Access bindings* at the
moment a browser would start: the binding is strict, a missing file is
that module's refusal at exactly this point (browser-free paths run
normally), and the measurement only informs the message. The **Figma
axis reads its `figma:` binding through the same lookup** — a design
check consults it before its first Figma read, same rules.

## Project facts, not guesses

Environment facts live in **`.claude/beyonder/environment.md`** (written
by `beyonder-setup`, found via [config-discovery.md](config-discovery.md)):
base URL and start command, login flow and test accounts, seeded-data
notes, the `Browser tool` field. Read it before touching the project's
app and cite it instead of guessing URLs or credentials. Browsing public
pages needs none of this; for the project's own app, ask once for URL and
login and recommend `beyonder-setup` — never invent credentials.

## The browser is a slot resource

The CLI parallelizes via named sessions, so every concurrent user
(subagents in `implement`, a review's content half, a walkthrough) MUST
pass its own `-s=<name>` on every command and close its own session when
done. Three rules make that safe — they exist because a shared tab
navigated by a parallel session silently invalidates whatever the other
session was looking at:

1. **Bind the session name to the run's identity** — the slot, branch, MR
   or run tag: `-s=<branch>`, `-s=mr-<iid>`, `-s=<run-tag>-content`. The
   default (unnamed) session is for interactive one-off use only; a
   skill-driven browser phase never uses it. A persistent profile, where
   one is needed, is per session (`--profile=<dir-per-session>`), never
   shared.
2. **Lock convention for unavoidable singletons.** An attached browser
   (`attach --cdp=…`, the Chrome extension) is **one** shared instance —
   named sessions do not isolate it. Browser phases on a singleton are
   **exclusive**: before navigating, create `tmp/browser.lock` (workspace
   root; content: session name + ISO timestamp). Lock present and fresh
   (< ~15 min) ⇒ another run owns the browser: wait, or degrade that phase
   with the named reason — never navigate over it. Remove your lock when
   the phase ends, also on error. A stale lock (dead run) may be taken
   over, and the report says so.
3. **Checkpoint artifacts as you go.** The browser is the least robust
   link in any run: sessions stall. Every screenshot, snapshot and
   console dump goes to disk the moment it is taken — explicit
   `--filename=` into the run's artifact directory, never held back for
   an end-of-run report. A session that dies mid-flow must cost the
   summary at most, never the evidence already gathered. And every
   screenshot caption names what is on the image that was **not**
   expected — the error box, the empty list, the odd layout — or says
   "nothing unexpected" explicitly. A caption that only repeats what the
   step meant to show is how a real bug ships inside its own evidence:
   in the 0.6.0 eval a setup screenshot showed an error box the caption
   never mentioned, and the box was a genuine bug.

## Where artifacts go, and what may age

Two destinations, and the difference is not cosmetic:

- **The CLI's own scratch** — `.playwright-cli/`, where every command
  without an explicit `--filename=` drops its output: page snapshots,
  `traces/`, `storage-state-<ts>.json`. Ours to clean, because it is
  output rather than configuration, and the committed SessionEnd hook
  ages it out (**older than 7 days**, per the CLI's own recommendation in
  `references/tracing.md`) instead of emptying it per session.
- **The run's artifact directory** — whatever the caller named:
  `implement`'s run directory `tmp/<ticket>/` in the main checkout
  (`../implement/SKILL.md` § *Isolation — every run stands alone*, point
  4), a review's `<scratchpad>/<run-tag>-artifacts/`
  ([content-checks.md](content-checks.md)). **Anything a report,
  ticket or MR note links lives here, always with an explicit
  `--filename=`.** No cleanup empties it — not teardown, not the hook,
  not a `git worktree remove`.

The two rules are one rule seen from both ends: artifacts the CLI dropped
by default may age away, and a linked artifact is never one of them,
because it was written to a place nothing ages. A report that links into a
directory some later cleanup may empty links into nothing.

**`state-save` needs a target, every time.** Bare `state-save auth.json`
writes `./auth.json` — into the repository root, and an auth state is a
credential. Pass a path into the run's artifact directory
(`state-save tmp/<ticket>/auth.json`), never a bare filename, and never a
path inside the reviewed workspace. `beyonder-setup` ① gitignores
`.playwright-cli/` for the same reason: the CLI's own default target for a
state save is inside it.
