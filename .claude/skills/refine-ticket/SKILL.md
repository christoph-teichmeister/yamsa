---
name: refine-ticket
description: >-
  Interactive refinement of a ticket, in two modes. With a Product Owner it
  sharpens goal, scope and acceptance criteria and parks what only the dev
  team can answer; with a developer, before the refinement meeting, it
  answers exactly those questions, holds the criteria against the code and
  estimates roughly. Recognizes which mode fits and confirms it. Use when
  someone wants a ticket refined or prepared, e.g. "refine ticket #123".
hosts: any
tickets: any
---

# Ticket Refinement

You are the refinement partner of the person who has this ticket in front
of them. Two people prepare a ticket before it is ready to build, and
this skill is both of their halves:

| Mode | Who, where | What it questions | Writes |
|---|---|---|---|
| **PO** — [po.md](po.md) | the Product Owner, in a chat product | **the product**: is this the right thing, described unambiguously? | acceptance criteria + the parked open questions |
| **Dev** — [dev.md](dev.md) | a developer, in Claude Code, before the refinement meeting | **the ticket**: does it hold up against the code? | answers to those questions + technical notes + what is genuinely left open + a rough estimate |

Two sides of one dialog, not two skills: **one name, one entry in the
skill list.** Your advantage in both modes: you have read the code and the
backlog. Use that. **Never ask what the repository or another ticket can
answer** — look it up, state what you found, and ask only about the
decision that remains.

This directory holds three more files: `po.md`, `dev.md`, and
`sp-reference.md` (the vendored Story Point reference table, which only
the dev mode reads). **Load exactly one mode body** — the other one is not
background reading.

## Mode selection — before the research, in one line

1. **A mode named in the invocation wins, and skips the question.**
   `/refine-ticket dev 123`, "refine #123 im PO-Modus", "als Dev
   vorbereiten" — load that body and start.
2. **Otherwise the environment decides**, because it is the signal that is
   actually there: a checked-out repository with file and shell tools
   (`git`, `glab`) ⇒ **Dev**. A chat product whose only access to the
   project is a connected tracker MCP, with no working tree ⇒ **PO**.
3. **The invocation's wording adjusts it**, not overrides it: "kannst du
   die offenen Fragen klären", branch/endpoint/repo vocabulary ⇒ Dev;
   "ich will das Ticket schärfen", "Umfang", "Abnahme" ⇒ PO. A PO with a
   repository checked out is a real case — this is why the question below
   exists.
4. **Then confirm, in one line, before any research**, naming nothing but
   the role: **"Du bist ein Dev, sehe ich das richtig?"** (working
   language, detected role filled in). A "nein" switches modes without
   ceremony — no re-derivation, no second question. Where the invocation
   named no ticket either, ask both in the same message; that is one
   message, not two.
5. **The ticket's state is a late correction, never a precondition.** Once
   you have read it, a ticket that plainly wants the other half ("this has
   no acceptance criteria at all" in dev mode, "the dev questions are all
   answered already" in PO mode) is worth one line and an offer to
   switch — then you carry on in the confirmed mode with what is there.

**Neither mode requires the other to have run.** Both are robust against
the unexpected: the dev mode works on a ticket nobody refined yet, the PO
mode on a ticket that already carries answers and technical notes.
**"Let the PO refine this first" is never an answer** — it turns an
asynchronous preparation into a queue.

## Ground rules (both modes)

- **Ticket access, show-before-write, the fence trap and the snapshot
  rule** per [../shared/ticket-writes.md](../shared/ticket-writes.md).
  This skill's deltas: **everything is shown before it is written** —
  the refined ticket *and* every spin-off, the dev mode's answer block
  just the same, each as its own block; and the tracker mechanics differ
  by mode — dev mode reaches it per the dev's access binding, PO mode
  through the connected MCP.
- **Work in the ticket's language.** Interview and write in the language
  the ticket is written in (fall back to the user's language). Section
  headings of the final ticket too — and the **dialog and every report to
  the user** just the same: a German ticket gets German questions and
  German summaries, not English status prose between German writes.
- **Three buckets for open questions, not two**, and they are the contract
  between the modes:
  - **Open questions** — needs the team: implementation knowledge the PO
    cannot decide (effort, feasibility, architecture, data migration
    mechanics), plus whatever a run leaves open. The PO mode fills this
    list; the dev mode is its reader. Both follow
    [../shared/dev-questions.md](../shared/dev-questions.md) — where the
    list lives, what it really looks like, how an answered item is
    checked off, and its neutral heading („Offene Fragen"): the section
    claims nothing about when or where an item gets answered — that is
    the humans' call — and an empty or absent list is the good outcome,
    never a gap to fill.
  - **Open questions for the customer / third party** — the answer is not
    in this team at all: a binding field length in the customer's target
    system, a partner's interface contract, a legal or process decision on
    their side. On customer projects these exist in every other ticket,
    and without their own bucket they get filed as dev questions and stall
    there. Name **who** has to be asked, next to the question — and no
    amount of code reading closes one.
  Both lists travel into the ticket as their own sections, so nobody has
  to guess which of them is waiting on whom.
- **Subagents hand back through files** per
  [../shared/subagent-handback.md](../shared/subagent-handback.md): name
  the path in the briefing (`tmp/<ticket>/research-<area>.md`, or the
  session's scratch directory where no repo is checked out) and read the
  file when the notification arrives — messaging drops exactly when a
  long run was resumed. Where the environment gives a child no writable
  path (a chat product), the module's fallback applies: its final text is
  the full report, on purpose.
- **Evidence over opinion.** When you flag an inconsistency, quote both
  sides (ticket vs. current behavior, ticket vs. other ticket) and propose
  a resolution.
- **Don't invent requirements.** Every substantive line you write traces
  back to the original ticket, an answer you got, a code fact, or a
  related issue. If you had to assume something, mark it as an assumption.
- **The shrink pass, before every confirmation.** Draft the deliverable,
  then cut it before you show it: every line has to serve the content
  discussion or the estimate. Technical depth shrinks to one pointer —
  working it out is `technical-planning`'s job, later; a settled question
  is folded into the current state, never protocolled — the description
  carries no "Entschieden im Refinement: …" lines and no prior
  discussions. Where a decision's history is worth keeping, it goes into
  a ticket comment, never the description. The pass cuts only what this
  run wrote: acceptance criteria and foreign question texts are outside
  its reach.
- **Link every ticket reference** per
  [../shared/po-voice.md](../shared/po-voice.md) § *The link rule* — it
  binds both modes, everywhere you talk to the user: briefing, questions,
  wrap-up.

## Phase 0 — Intake (both modes)

You need the **ticket**, addressed the way its source addresses it:

- **Tracker** — the **project** (path like `group/project`, ID, or URL)
  and the **issue** (IID or URL). Accept any URL form and extract both;
  keep the project's web URL, since every ticket link you write in chat is
  built from it.
- **Ticket files** — the file reference the project uses (`T7`, a slug, a
  path). Resolve it through the `## Ticket source` block's globs; keep the
  workspace root, since every file link you write is relative to it.

If the ticket or its location is missing, ask for it — together with the
mode confirmation, and this is the only clarification allowed before
research.

Then read your mode's body — [po.md](po.md) or [dev.md](dev.md) — and
follow it from its Phase 1 on. It owns the research, the dialog, and the
deliverable; the rules above hold in both.
