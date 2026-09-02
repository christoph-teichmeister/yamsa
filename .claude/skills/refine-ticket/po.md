# Mode body — refinement with the Product Owner

Loaded by [SKILL.md](SKILL.md) when the PO mode is confirmed; its ground
rules and Phase 0 hold here and are not repeated. Together with the PO you
take a draft ticket to the state where a PO's work on it is *done*: the
goal is unambiguous, scope is bounded, acceptance criteria are testable,
every product decision is made — and everything a PO legitimately *cannot*
decide is parked as an explicit open question for the dev team.

## Ground rules of this mode

- **Ask the PO only what a PO can decide:** goals, users, scope, desired
  behavior, priorities, trade-offs. Everything else goes into one of the
  two parked buckets (SKILL.md) — tell the PO in one line when you add
  one, and move on. You never ask the PO a technical question, not even a
  small one.
- **The PO voice** per [../shared/po-voice.md](../shared/po-voice.md) —
  speak product never code, the self-check before every message, the
  link rule. This mode's deltas: technical detail has exactly three
  places to live — the "Notes for implementation", "Open questions" and
  "Open questions for the customer" sections of the final ticket. (This rule is *this* mode's; the dev mode talks code on
  purpose.)
- **The ticket describes the problem, not the solution.** If the draft
  prescribes implementation details, ask whether that's a real constraint
  or an idea — ideas move to a non-binding "notes" line or are dropped.
- **Tool names vary by MCP server.** Use whatever the connected GitLab MCP
  exposes for reading, searching, writing, and reading files. If a
  capability is missing (e.g. no code search), degrade gracefully: say
  what you couldn't check and continue with the rest.

## The re-refinement fork

A ticket that carries the marks of an earlier refinement — the
deliverable's section structure, an open-questions list, a refinement
comment — is **not** refined from scratch. Say what you found and ask
which mode (`Empfehlung:` update):

- **Update** (default) — the agreed content stands. You verify it, then
  refine only what genuinely moved: new information, ACs that reality has
  overtaken, open questions the dev team has since answered. Every
  interview question names why it is being asked *again*.
- **Replace** — the ticket is refined from zero, and the PO knows the
  earlier decisions are on the table again.

Update mode has a procedure — the same one `technical-planning` follows
for its plans: **verify the references, correct only what you can
evidence.** Concretely: check every claim the ticket makes about the
current system (and about *its own* implementation status) against the
code and the tracker before you build on it. A ticket that says "the
export already runs nightly" or has ACs ticked off is making a claim, not
stating a fact — a **stale status** is the most expensive thing a
refinement can carry forward, because everything after it is planned
around something that does not exist. What you cannot confirm becomes a
question or a marked assumption; what you disprove, you quote both sides
of. Do not silently modernize wording the PO once agreed to.

Marks of a **dev refinement** — answered questions, technical notes, an
estimate — are not marks of a PO refinement: they are the other half of
the dialog, and they are input, not something to redo. Read them, use
their answers to strike questions you would otherwise have asked, and
leave the notes standing.

## Phase 1 — Research (silent)

Do all of this *before* asking the PO anything:

1. **The ticket itself** — title, description, labels, milestone,
   epic/linked issues, and all existing comments. Comments often contain
   decisions already made; treat those as settled unless they contradict
   each other.
2. **The rest of the open backlog** — run the shared
   [feasibility-check module](../shared/feasibility-check.md) in
   `single` mode: duplicates, overlaps, contradictions with the other
   open issues (same milestone/epic first). Separately, note the
   dependencies this ticket has or creates.
3. **The relevant code** — search for the domain terms, entity names, UI
   strings, and route/feature names the ticket mentions; read enough of the
   relevant files to know how the feature behaves *today*: existing
   validation rules, states, permissions, empty/error handling. This is
   where real edge cases come from.
4. **Recent merge requests** touching the same area (optional, if cheap) —
   in-flight changes the ticket should account for.
   **Stale-status check** (always, and mandatory in update mode): for
   every state the ticket claims already exists — a shipped feature, a
   ticked-off AC, "wird bereits so gemacht" — confirm it in the code or
   the tracker. Confirmed ⇒ nothing to do. Contradicted ⇒ that is a
   finding for the interview, with both sides quoted. Unconfirmable ⇒ it
   travels as a marked assumption, never as a fact.
5. **Size check** — is this ticket plausibly one increment, or several?
   Signals: more than one user-facing goal, ACs that test different
   features, "and also …" scope, work for several distinct screens or
   roles. If it looks too big, sketch the natural cut lines now and run
   every candidate through [../shared/ticket-split.md](../shared/ticket-split.md):
   evidence first, verdict from the evidence, and only then the artifact —
   spin-off ticket, icebox note, or the conservative outcome where the
   ticket keeps everything and a seam in the implementation does the
   separating. The interview confronts the PO with the result, one
   question, per that module's forms.

Stay targeted. Read what the ticket points at, not the whole repository;
a handful of well-chosen searches beats an inventory.

Research findings are raw material, not content. Most of what you learn
here is never said to the PO — it shapes which questions you ask, which
edge cases you probe, and what goes into the dev notes of the final
ticket. Resist the urge to prove how much you read.

## Phase 2 — Briefing

Before the first question, one short message whose only job is: let the
PO confirm you read the right ticket the right way. Hard format:

1. **Intent** — the ticket's goal in your own words, one sentence.
2. **Today** — what a user sees or can do today, one sentence ("gibt es
   noch nicht" is a complete answer).
3. **Related** — one line total, only tickets that constrain this one:
   `[#iid](link) (status in one word)`. Skip the line if none do.
4. **To settle** — the interview's 2–4 topics as a comma-separated list
   of keywords ("Umfang, Design-Vorlagen, Reihenfolge"), not sentences.
   If the size check flagged the ticket, "Zuschnitt" is one of them.

Four to six lines, then question 1 follows in the same message. No
analysis, no verdicts on whether the ticket is justified, no evidence,
no "biggest gaps" prose — every research finding you're tempted to put
here belongs inside the one question that turns on it, and is wasted
anywhere else. A PO who wants the long version will ask.

## Phase 3 — Interview

Grill-me rules, adapted for POs:

- **One question at a time, and keep it small.** Fixed shape: a short
  bold label (`**Frage 3 — Edge case:**`), at most one sentence of
  context — the single fact this question turns on, nothing more — the
  question itself, then `Empfehlung:` with the answer you'd give in one
  sentence, phrased as desired behavior or ticket wording, never as how
  to build it. Three sentences, roughly 60 words, no bullet lists or
  headings inside a question. Add reasoning only when the recommendation
  isn't obvious from the context sentence, and then as one subordinate
  clause. The goal is that the PO can answer "ja" — a recommendation
  that itself needs reading twice defeats the format.
- **One decision per question.** No "… oder soll zusätzlich X?" tails —
  if the answer opens a follow-up, that's the next question. If a
  question needs long setup, you're explaining implementation, not
  asking a product question: split it or park it as a dev question.
- **Most load-bearing first.** Goal and user value → cut (if the size
  check flagged it) → scope (in/out) → desired behavior and acceptance
  criteria → edge cases → dependencies and sequencing → non-functional
  needs (permissions, performance, rollout).
  A session cut short must still have settled the big rocks.
- **Resolve each branch before moving on**, and never re-ask a settled
  decision. Answers can invalidate earlier assumptions — when one does,
  say so and revisit that one point.
- **Derive edge cases from the code**, not from a generic checklist: the
  validation constants, state machines, empty states, and error paths you
  found in Phase 1 each imply a product question ("today an X without Y is
  rejected — should that stay true here?"). Ask for the desired behavior
  in product terms.
- **Confront inconsistencies directly**: ticket vs. code, ticket vs.
  another open ticket, ticket vs. its own comments. Quote both sides,
  recommend a resolution.
- **Guard the scope, propose the cut — conservatively.** If the size
  check (or the interview) shows the ticket is really several, present
  the Phase 1 result as **one** question: what the ticket keeps, then one
  line per candidate — and per candidate the **reason before the
  artifact**, in the order
  [../shared/ticket-split.md](../shared/ticket-split.md) prescribes.
  A candidate whose evidence disqualifies it is not offered as a spin-off
  at all; it is offered as the seam form, with that evidence as the
  reason. `Empfehlung:` included. Same for requirements that creep in
  mid-interview and belong elsewhere. Agreed spin-offs become real
  tickets in Phase 4.
- **Questions about an agreed spin-off leave the interview.** Once a cut
  is agreed, everything that would refine the *spin-off* goes into that
  spin-off's own open-questions list (announce it in one line) — this
  interview refines the ticket that keeps the core, nothing else.
- Technical unknowns surfacing along the way go to the dev-questions list
  (announce it in one line), not to the PO.
- **Bundle the low-stakes tail.** A human PO's patience is the budget.
  When the genuinely branching decisions are settled and what remains is
  small items with obvious answers, stop asking them one by one: bundle
  them into **one** confirmation round with stated defaults ("Ich nehme
  an: X, Y, Z — Einwände?"). Anything the PO objects to becomes a
  regular question; silence on the rest is the answer.

The interview ends when every branch is resolved — then ask the closing
question: **"Is there anything we haven't covered yet that could affect
this ticket?"** Only after that, produce the deliverable.

**Quick mode:** if the PO asks for a one-shot review instead of the
interview ("just give me feedback"), skip Phase 3: deliver the briefing,
your findings (split proposal included), and the revised ticket in one
message, with every unconfirmed decision marked as an assumption — and
write **nothing**: without confirmed decisions there is nothing to apply.

## Phase 4 — Deliverable

Show the finished ticket as **one fenced code block** of GitLab-flavored
markdown:

- **User story** — As a …, I want …, so that … (who benefits and why; if
  the original had a good one, keep it).
- **Context** — why now, links to related issues as `#<iid>`, relevant
  current behavior in one or two sentences.
- **In scope / Out of scope** — explicit bullets; out-of-scope names the
  spin-off tickets if a split was agreed.
- **Delivery** *(only where the agreed outcome was the seam form)* — the
  parts, their order, their AC coverage and the seam reason, exactly as
  [../shared/ticket-split.md](../shared/ticket-split.md) Form C spells
  it out. This is what "it stays in the ticket and a PR seam separates it"
  looks like on paper; without it the decision is lost by the time anyone
  builds.
- **Acceptance criteria** — GitLab task list (`- [ ]`), each criterion
  independently testable, covering the decided edge cases.
- **Notes for implementation** *(only if needed)* — non-binding pointers
  (e.g. file paths you found, the constraint behind a prescribed detail).
- **Open questions** *(only if any)* — task list (`- [ ]`) of everything
  parked during the interview; each question in one sentence, with the
  context a dev needs to answer it. This section is read by the dev mode
  and by `technical-planning` — its shape and neutral heading are the
  contract in [../shared/dev-questions.md](../shared/dev-questions.md).
  Items a dev run already answered keep their answer line; you do not
  re-open them. Nothing parked ⇒ no section.
- **Open questions for the customer** *(only if any)* — same shape, plus
  **who** has to be asked: the questions this team cannot answer at all.
  Keeping them out of the dev list is the whole point — a dev list holding
  a question nobody in the team can answer stalls quietly.

Preserve the original's substance and tone — this is a refinement, not a
rewrite for style points. If a split was agreed, show each spin-off as
its own short block (title + first-format description) — a spin-off
whose content was never shown does not get written, full stop. What you
show is the draft **after** the shrink pass (SKILL.md's ground rule) —
the PO confirms the short version.

Then one confirmation question (`Empfehlung:` apply it). This question
is never skipped — not even when the PO's closing message already
sounded like a go-ahead (SKILL.md's ground rules). On confirmation,
through the write path the ticket source names, each write confirmed in
one line with the link (tracker) or the **path** (file):

1. **Update the ticket's description** with the refined version — on a
   tracker via the MCP's description update; on a file ticket by editing
   the file's description section, with the fence trap in mind
   (`ticket-writes.md`: the block above is presentation, never payload).
2. **Create the agreed spin-off tickets** and link them to this one — on a
   tracker whatever link relation the MCP supports (otherwise a "related:
   #iid" line in the descriptions); on file tickets a new file at the
   location and naming pattern the `## Ticket source` block records, with
   a "related: `<reference>`" line on both sides.
3. **Update the ticket index, if the project has one.** Where the
   `## Ticket source` block names an `index:` file (a
   `00_Ticket-Uebersicht.md` and the like), it is part of the ticket
   source, not decoration: a refined ticket whose one-line summary or
   status in the index still says the old thing is actively misleading —
   people read the index precisely to avoid opening every file. Amend the
   affected rows (this ticket, plus a row per new spin-off), touch nothing
   else, and name the path in the confirmation. No `index:` entry ⇒
   nothing to do.

After the writes, outside the block, briefly:

1. **What changed** vs. the original ticket, in a few bullets.
2. **Manual steps for the PO** — only what the write path couldn't do: adjust
   labels/milestone if needed, plus anything from a degraded write path
   (paste the description, create a spin-off by hand). If the team keeps
   a planning board (Miro, physical, …), add the hand-over line: new
   spin-off cards and changed scope/estimates need syncing there — you
   stop at the ticket boundary.
3. **Handover** — one line: the ticket is ready for the dev team's
   preparation (this skill's dev mode before the refinement meeting,
   `technical-planning` immediately before the build).
