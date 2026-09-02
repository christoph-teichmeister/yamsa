# Shared module — splitting a ticket, and the seam that isn't a split

Not a skill entry. This module is run *inside* another skill
(`refine-ticket`'s two modes, `technical-planning`) and answers one
question: this ticket looks like more than one increment — **what comes
out of that?** Three outcomes, each with a form. The calling skill
decides which; this module fixes what the deliverable then looks like.

## The gate: the reason comes before the proposal

Per candidate, in this order — the order *is* the rule:

1. **Evidence.** What does the candidate need from the rest, and what
   does the rest need from it? Quote it: the acceptance criterion, the
   ticket line, the code fact. "Nothing in either direction" is a
   complete answer and has to be *said*, not left out.
2. **Verdict from that evidence.** Independently buildable **and**
   independently prioritizable? A hard sequential dependency — the
   candidate is unbuildable or unprioritizable until the rest lands, or
   the remainder loses its user value without it — makes it **not** a
   spin-off.
3. **Only then the artifact**, per the forms below.

A candidate whose evidence line is not written is not proposed. And the
disqualifying fact belongs to step 1, never into the same sentence as the
proposal: once "this only becomes buildable after the core lands" has
been written down, the candidate does not reach step 3 as a spin-off at
all. That sentence is the whole check — a run that names it *while*
proposing the split has skipped it.

## Form A — spin-off ticket

For a candidate that survived step 2: its own title, a first-format
description, its **own testable acceptance criteria**, and a relation line
to the original on both sides. It is shown in full before anything is
written (the calling skill's confirmation rule), and the original's *out
of scope* names it. **The evidence from step 1 is shown with the
proposal** — one clause, "independent because …" — so the reader can
check the verdict instead of taking it.

## Form B — icebox note

Worth remembering, not plannable yet: no ticket, no acceptance criteria,
no estimate. A note in the place the project keeps them. Offer the
artifact that fits rather than promoting the note to a ticket because a
ticket is the shape you have.

## Form C — one ticket, two parts, a seam in the implementation

The conservative outcome, for a candidate with a hard sequential
dependency: **nothing is created, nothing moves out**, and the separation
happens during implementation instead. Deliverable form, in the ticket:

```
## Delivery
Part 1 — <name>: <what it delivers, in one line>. Covers AC 1–4.
  Seam: <the boundary — its own MR, or its own commit series>.
Part 2 — <name>: <what it delivers>. Covers AC 5–7.
Seam reason: <the dependency that made this a seam and not a split,
  with its evidence>.
```

- **Parts, not tickets.** No `#iid`, no milestone, no estimate of its
  own, and *out of scope* stays untouched: both parts are in scope. Every
  acceptance criterion belongs to exactly one part, addressed by its
  position in the AC list, so each part is verifiable on its own.
- **The build order is the part order**, and the seam sits between them.
- **Delivery vocabulary follows the project** (`workflow.md`'s
  `Push policy`): with `commit only` there is no MR to promise — the seam
  is then a commit series per part.
- **The seam reason is load-bearing, not decoration.** It is the record
  that stops the next run from proposing the spin-off this one just
  rejected.

## Carrying an existing seam forward

A ticket that already names its parts has been cut. The later skill does
not re-cut it: it reads the parts, keeps their order and their AC
mapping, and groups its own deliverable by them (`technical-planning`: one
task group per part, the seam as the heading between the groups). Where a
finding genuinely breaks the existing seam, say so with the evidence and
propose the new one — as a change to a recorded decision, not as a fresh
idea.
