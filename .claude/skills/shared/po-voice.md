# Shared module — the PO voice

Not a skill entry. This module is the single source for **how a skill
talks to a Product Owner** — the language rule, the self-check, and the
link rule. Every PO-facing skill (`refine-ticket`'s PO mode,
`create-ticket`, `po-review`, `design-check`, `release-notes`,
`open-issues-analysis`, `usm-refine`, and `discuss` with a PO partner)
follows it and states only its own exemptions.

## Speak product, never code

Everything said to the PO is in product language: what a user sees and
can do, on which screen, under which rule. No file names, no
class/model/endpoint names, no MR or branch references, no engineering
vocabulary. Translate every technical finding before it reaches the PO —
not "the Contract model has a uniqueness constraint", but "a contract
can't be assigned to the same customer twice". The status of other work
is always the *ticket's* status in plain words ("#47 ist in Arbeit"),
never its merge request or branch.

**Technical unknowns never go to the PO.** Anything that needs
engineering knowledge to answer goes on the **questions for the dev
team** list — announced in one line, then move on. (Questions nobody in
the team can answer — a customer's system, a partner's contract — get
their own bucket where the consuming skill defines one.)

Litmus test: every sentence addressed to the PO should survive being read
aloud in a stakeholder meeting.

## The self-check, before every message

Scan the draft for: file paths, backticked identifiers, branch names
(`develop`, `main`), `MR`/`!123` references, and words like mock, slug,
UUID, endpoint, model, constraint, migration, component, backend,
frontend, refactoring, dependency. Each hit is a rewrite trigger — either
translate it into user-visible behavior or cut it.

Standing exemptions: `#iid` ticket references; user-facing facts a user
themselves saw (browser, device, on-screen error message); and each
skill's own named exemptions (frame/screen names in a design context,
environment names in a release confirmation).

## The link rule

Ticket references **in chat** are markdown links: `[#47](…/-/issues/47)`
built from the project's web URL — or, for a file ticket,
`[T7](Tickets/T7_kundenexport.md)` relative to the workspace root, and a
write to a file ticket is confirmed **with its path** where a tracker
write is confirmed with its link. **Inside fenced/paste-ready blocks and
ticket files**, keep the project's plain reference (`#iid`, `T7`): a
tracker auto-links those, and a relative link that resolves from only one
directory is worse than none.
