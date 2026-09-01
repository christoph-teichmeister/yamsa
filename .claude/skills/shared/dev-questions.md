# Shared module — the questions parked for the dev team

Not a skill entry. This module is run *inside* another skill
(`refine-ticket`'s dev mode, which exists to answer this list;
`technical-planning`, which answers some of it as a by-product of
planning) and governs one artifact: the list of questions a PO-facing run
parked because only the dev team can answer them — **how to find it, and
what happens to an item that gets answered.**

Two skills touch the same list. They use the shape below, so a ticket
touched by both reads as one list instead of two conventions.

## Where it is, and what it really looks like

Seven skills write this list; none of them normalized it. Do not go
looking for one form:

- **`refine-ticket`'s PO mode writes it into the ticket description** as
  its own section, as a GitLab task list (`- [ ]`).
- **`po-review`, `design-check`, `open-issues-analysis`, `usm-refine`,
  `release-notes` and `discuss` produce it inside a paste-ready block** — a
  human then pastes it as a **comment** or carries it into a meeting. There
  the items are plain one-sentence bullets, not check boxes.

So: read the description **and** the comments, and treat both forms as the
list. The heading the ticket-writing skills **write** is neutral, in the
ticket's language: `Offene Fragen` / `Open questions` — it claims nothing
about when or where an item gets answered; that is the humans' call, not
the ticket's. Older tickets and report blocks carry
`Open questions for the dev team`, `Questions for the dev team`,
`Fragen ans Dev-Team` — read them all as the same list. The section is
optional in every deliverable: an empty or absent list is the good
outcome, never a gap to fill. Where the same question exists in a comment
and in the description, the description is the current version — say that
in one line and work on that one.

**The neighbouring section is not yours.** `Open questions for the
customer` / `Klärung beim Kunden` (and `technical-planning`'s
*clarification with the customer*) name a question whose answer is not in
this team at all. No amount of code reading answers it. Leave those items
untouched, including their boxes.

## Answering one: the check-off shape

```
- [x] <the question text, unchanged> — **beantwortet:** <the answer in one
      sentence> (<where the reasoning lives: plan section, comment, notes>)
```

Plain-bullet lists get the same line with a leading `✓` instead of the
box. The label follows the ticket's language (`answered:`,
`beantwortet:`).

- **The question text is never rewritten**, never reordered, never
  deleted, never moved into another section. The list is somebody else's
  record of what they did not know; its value is that it is still
  recognizable.
- **Only evidence checks a box.** A question is answered when a code
  read, a ticket, or a decision taken in this run answers it — the
  pointer says which. A question that merely lost its relevance is closed
  as `— entfällt: <reason>`. A question you did not resolve stays exactly
  as it is; an unticked box is a valid, honest state.
- **The answer itself lives outside the list.** One sentence in the item,
  the reasoning where the run's substance is (the plan, the notes
  section, the comment) — a list item that grows into three paragraphs
  stops being a list.
- **New questions append to the existing list**, unmarked — the
  description holds the current state, not a protocol; where a round's
  history is worth keeping, it goes into a ticket comment, never the
  description. A second list next to the first is how a ticket ends up
  with two half-answered ones.
