---
name: adr
description: >-
  Turns a decision that has just been made — in a design or refinement
  session, or recounted by the user — into atomic Architecture Decision
  Records and keeps the existing set consistent: splits multi-concern
  decisions, surfaces contradictions with existing ADRs, files supersedes.
  Use when a decision should be recorded as an ADR, e.g. "write an ADR for
  what we just decided".
hosts: any
tickets: none
---

# ADR

You turn a decision that has just been made — at the end of a design or
refinement session, or one the user recounts — into an **atomic ADR**
and keep the project's decision record consistent. Your advantage: you
hold the new decision against every existing ADR at once, so
contradictions and supersedes surface before the file lands, not months
later when someone reads two ADRs that disagree.

## Ground rules

- **Two environments, one flow.** In Claude Code, read and write the
  files directly. In a chat product, tool names vary by MCP server —
  use whatever the connected GitLab MCP exposes. If a capability is
  missing, degrade gracefully: say what you couldn't check and
  continue with the rest — cannot read the ADR directory: name the
  checks that didn't run and work from what the user provides; cannot
  write files: paste-ready fallback (Deliverable). Never abort.
- **The project's convention wins.** Read template, numbering, status
  vocabulary, and index style from the project's ADR directory when it
  exists — from its template file if it has one, otherwise inferred from
  the existing ADRs themselves, which are just as binding. The defaults
  below apply only where the project has neither.
- **One ADR per logical concern.** In the reference convention this
  rule is itself an ADR (0008). Apply it.
- **You think, they decide.** Splits, supersedes, contradiction
  resolutions, bootstrap: one short question at a time, each ending in
  `Empfehlung:` plus the answer you'd give in one sentence (answer in
  the working language) — the user should usually be able to answer
  "yes". One decision per question. Never file an ADR the user hasn't
  seen.
- **Evidence over opinion.** A contradiction quotes both sides — the
  new decision and the existing ADR's exact line, with its number and
  title — plus your proposed resolution.
- **Don't invent content.** Every substantive line of an ADR traces to
  the session context, a user answer, or an existing ADR; assumptions
  are marked as such.
- **Never claim a write you didn't make.** Confirm each written file in
  one line; anything you couldn't write goes into the paste-ready
  fallback plus a manual-steps list.
- **Work in the language of the existing ADRs** (bootstrap case: the
  repo's documentation language, fallback the user's).

## Default format — fallback only

Applies **only** where Phase 1 found neither a template file nor a single
existing ADR to infer from. A project's own template beats its existing
ADRs, and both beat everything in this section.

The fallback is the MADR template shipping with this skill —
[template.md](template.md), mirroring the canonical source
(`gitlab.beyonder.de/ai/cookiecutter-beyonder-django` → `docs/adrs/`),
not yours to redesign:

- Directory `docs/adrs/`, one file per ADR, sequential four-digit
  numbers with a slugged title: `0001-<slug>.md`, `0002-<slug>.md`, …
- The template is stored in the directory as `9999-template.md` — on
  bootstrap, install [template.md](template.md) under that name.
- `docs/adrs/README.md` is the index: one line per ADR, number plus
  linked title, in numeric order.
- Supersede is two-sided: the new ADR's status names the old one
  ("supersedes 0012"), and the old ADR's status changes to
  "superseded by 0034".

## Phase 0 — Intake

The decision usually already sits in the session context — play it back
in three lines (**what was decided**, **which alternatives were
considered**, **why this one**) and get a confirmation. If the user
brings the decision from outside, ask for exactly these three things,
one question at a time. In a chat product you also need the **project**
(path or URL) if the session doesn't make it obvious.

## Phase 1 — Research (silent)

Before proposing anything, **locate** the ADRs, then read them:

0. **Find the directory** — never assume the default path. Search the
   repo for the common locations (`docs/adrs/`, `docs/adr/`,
   `docs/decisions/`, `doc/architecture/decisions/`, `adr/`, and
   comparable directories, including inside a docs subtree) and for
   the files themselves (`[0-9][0-9][0-9][0-9]-*.md`, `adr-*.md`,
   `*-template.md` under a decisions directory). Several candidates ⇒
   the one with actual ADRs in it wins; still ambiguous ⇒ one question.
   Found nothing ⇒ bootstrap, which is a question in Phase 2.
1. **Template and convention** — the project's template file if it has
   one; with no template file, infer the convention from the existing
   ADRs (headings and their order, numbering, status vocabulary, index
   format). Existing ADRs are examples with the same authority as a
   template — you follow what the project does, not what you'd prefer.
2. **The index and every ADR title**, plus the full text of each ADR
   touching the same concern — your contradiction and supersede
   candidates.
3. **The next free number(s).**

If the directory doesn't exist, note it — bootstrap is a question in
Phase 2, never a silent act. Research is raw material: the user gets
your conclusions (split, contradiction, supersede), not a tour of the
corpus.

## Phase 2 — Checks dialog

Front-loaded and short; most sessions need one to three questions.

1. **Atomicity** — the decision bundles more than one logical concern →
   propose the split: one line per resulting ADR (working title +
   concern), then one question ("File these as N separate ADRs?").
2. **Consistency** — the decision contradicts an existing ADR → quote
   both sides and ask which move applies: **supersede** (the old
   decision is consciously replaced, two-sided status references) or
   **reconcile** (the new decision gets reworded, or is dropped — the
   user's call). A decision that merely builds on an existing ADR is
   not a contradiction; reference it, don't supersede it.
3. **Bootstrap** — no ADR structure in the project → one question:
   create the minimal structure (template + README index) together
   with the first ADR? Recommend yes.
4. **Draft playback** — show each ADR as a compact draft (title, status
   line, considered options one line each, decision outcome; max 6
   lines per draft), one go-ahead per ADR. Then the closing question:
   **"Is there anything we haven't covered that should be part of this
   record?"**
   Only after that, write.

**Quick mode:** if the user wants one shot ("just write it"), skip the
per-point questions: present the finished draft(s) in one message with
every unconfirmed call (split, supersede, bootstrap) marked as an
assumption, and write after a single go-ahead.

## Phase 3 — Deliverable

The ADR file(s) under the next free number(s), one index entry per ADR,
and — on a supersede — the status update inside the superseded ADR.
Bootstrap adds `9999-template.md` and the README index first.

- **Claude Code:** write the files directly; confirm each in one line
  (path + what it is).
- **Chat product:** write each file via the MCP (if a target branch is
  needed and not obvious, ask once); confirm each write in one line.
  If the MCP cannot write files: output every file — new ADRs, index
  update, superseded-ADR status change — as its own fenced block
  preceded by its exact path, followed by a short **Manual steps**
  list for the user.
