---
name: glab
description: >-
  GitLab access for dev skills and direct lookups via the glab CLI: issues,
  merge requests, threads, pipelines, raw API. Writes are allowed as far as
  the token's scope goes. Use when someone wants GitLab information or
  actions from the terminal, e.g. "show issue 123".
user-invocable: false
hosts: [gitlab]
tickets: none
---

# GitLab CLI (glab)

You are the GitLab access of the dev toolchain — for the dev asking
about an issue, and for the other skills (`implement`,
`technical-planning`, `pipeline-doctor`, the mr-review family) that
route their GitLab reads and writes through the same rules.

## Ground rules

1. **The dev's binding decides the access path — strictly.** Read the
   `gitlab:` line of `.claude/beyonder/access.local.md` `## Access`, per
   [../shared/config-discovery.md](../shared/config-discovery.md)
   § *Access bindings*: `cli` ⇒ every operation runs through `glab`;
   `mcp` ⇒ every operation runs through the connected GitLab MCP. The
   other tool is never used, not even as a fallback — when the bound way
   fails (binary gone, auth expired, MCP down), say so in one line,
   deliver the content paste-ready, and move on. **No
   `access.local.md`** ⇒ refuse at this first GitLab call with the
   module's canonical fix line; the binding's measured state and date
   make that message concrete ("bound to MCP, measured read-only — writes
   will 403").
2. **Verify before the first call:** for `cli`, `command -v glab && glab
   auth status`; for `mcp`, that the server is connected. Failure ⇒ the
   degrade in rule 1, never a tool switch.
3. **Writes are legitimate** (create issues/notes, update descriptions,
   resolve threads, trigger retries) — when the task calls for them and
   the user confirmed anything user-facing. A `403`/permission error
   means the token lacks scope: say so in one line, deliver the content
   paste-ready, move on. Never claim a write that didn't happen.
4. **Project context:** default to the repo's remote; an explicit
   `group/project` in the request overrides it (`-R` flag).

## Auto-detect the ticket from the branch

For "this issue"/no arguments: read `git branch --show-current` and
extract the issue number using the project's branch convention
(`.claude/beyonder/workflow.md`, fallback: the common pattern
`<type>/#<number>-<description>`). On the default branch or no match,
ask for the number.

## Command reference

Adapt flags freely; `--help` beats guessing.

| Use case | Command |
|----------|---------|
| View issue (+ comments) | `glab issue view <n> [--comments]` |
| Create/update issue | `glab issue create` / `glab issue update <n>` |
| Comment on issue | `glab issue note <n> -m "…"` |
| View MR (+ comments / unresolved) | `glab mr view <n> [--comments] [--unresolved]` |
| MR diff (+ stats) | `glab mr diff <n> [--stat]` |
| Pipeline status (branch / current) | `glab ci status [--branch <b>]` |
| Job logs | `glab ci trace <job-name>` |
| Retry pipeline/job | `glab ci retry …` |
| Raw API | `glab api <endpoint> [--method POST -f k=v]` |

## Pipeline debugging flow

1. `glab mr view` (auto-detects the current branch's MR — none found ⇒
   say so)
2. `glab ci status`
3. `glab ci trace <failing-job>` for the error lines
4. Summarize: failing job, stage, relevant error lines. (For the full
   diagnose-and-fix loop, that's `pipeline-doctor`.)

## Output guidelines

- Summarize, don't dump raw CLI output.
- Issues/MRs: title, status, assignee, labels, key description points.
- Pipelines: failing job, stage, the error lines that matter.
- Offer to fetch more (comments, full diff) instead of preloading it.
