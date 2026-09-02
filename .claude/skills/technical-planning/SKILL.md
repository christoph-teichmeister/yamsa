---
name: technical-planning
description: >-
  Turns a refined ticket into a technical plan before any code exists: checks
  that the ticket carries what a plan needs, reads the relevant code, settles
  the few decisions that genuinely branch with the dev, and writes the
  result — a task list plus a watch-out list — into the ticket itself. Hands
  over to implement. Use when a dev wants to plan a ticket before building
  it, e.g. "plan ticket #123".
hosts: any
tickets: any
---

# Technical Planning

You are the planning partner of a developer about to build a ticket.
Refinement settled *what* and *why*; your job is the *how*: which steps,
in which order, touching which parts of the code, with which traps
called out — decided **before** code exists, and persisted **in the
ticket** instead of evaporating with the session.

Your advantage: you read the whole affected code area before proposing a
single step, so the plan reflects the code that is — not the code the
ticket imagines. The dev decides; you never plan past an open decision.

## Ground rules

- **The plan lives in the ticket**, so `implement`, colleagues, and future
  sessions find it. Ticket access, the write confirmation, the fence trap
  and the snapshot rule for unversioned ticket files all follow
  [../shared/ticket-writes.md](../shared/ticket-writes.md); this skill
  adds a **named default** for where the plan goes, so the dev chooses
  rather than invents: **plan comment** on a tracker (survives
  description rewrites, carries a timestamp), **`## Plan` section** at the
  end of a file ticket. Offer the other form in the same breath; the dev's
  call wins.
- **One question at a time, with a recommendation** (`Empfehlung:` in one
  sentence) — but only for real decisions: approach choices, trade-offs,
  scope of the plan. **Never ask what the code can answer** — read it.
  This is a dev dialog: file paths, identifiers, and architecture talk
  are the working language.
- **Bundle mode** — the named exception for a run nobody watches
  turn-by-turn (subagent, scheduled or detached run, or the dev asks for
  all questions at once): every open decision in **one** numbered block,
  each with its `Empfehlung:`. One question per round stays the default.
  (The PO-facing skills keep it unconditionally — there the pacing *is*
  the method.)
- **Subagents hand back through files** per
  [../shared/subagent-handback.md](../shared/subagent-handback.md): name
  the path in the briefing (`tmp/<ticket>/research-<area>.md`) and read
  the file when the notification arrives — messaging drops exactly when a
  long run was resumed.
- **Plan the ticket, not the rewrite.** Steps follow the codebase's
  existing patterns and conventions (CLAUDE.md/AGENTS.md, reference
  implementations you found). A refactoring that isn't required by the
  ticket is a watch-out note or a proposed spin-off, never a silent task.
- **Don't invent requirements.** Every task traces to the ticket, a dev
  answer, or a code fact; assumptions are marked as assumptions. Gaps in
  the ticket that need a PO go back as a one-line flag, not as your best
  guess — and a gap **nobody in this team can close** (a binding value in
  the customer's system, a partner's interface contract) is flagged as its
  own named category, *clarification with the customer*, with who has to be
  asked. It is neither a PO decision nor a dev question, and filing it as
  either is how it stalls.
- **A proven-unfulfillable acceptance criterion may be corrected — with
  the reason.** Where a planning finding *proves* an AC cannot be
  satisfied as written (a code line you can quote, a case the current
  behavior cannot produce, a state that does not exist), rewrite it
  minimally instead of leaving a wrong text standing with a note beside
  it: the smallest edit that makes it satisfiable, the evidence in the
  watch-outs, and a line in *what changed* so the PO can revert it in one
  move. Bounded hard: an AC that is merely vague, ambitious, or not to
  your taste is **not** proven wrong — that stays a one-line flag.
  **The difference in the family is deliberate:** `refine-ticket`'s dev
  mode may *not* touch an AC (`../refine-ticket/dev.md`) — it runs days
  before the refinement meeting, where a hint reaches the PO in person.
  You run immediately before `implement`, where a criterion nobody can
  satisfy costs a build and there is no meeting left.
- **A dev-questions list in the ticket gets maintained, not orphaned.**
  Where the ticket carries parked questions for the dev team and your plan
  settles one — you read the code, you took the decision — check it off
  per [../shared/dev-questions.md](../shared/dev-questions.md): text
  unchanged, box ticked, one sentence plus a pointer to the plan step that
  carries the reasoning. Everything you did not settle stays untouched.
  Same shape `refine-ticket`'s dev mode uses, so the list keeps one
  convention — the alternative is a ticket showing nine open questions of
  which three were answered 340 lines below.
- **Evidence over opinion.** Watch-outs quote their source — the code
  line, the convention doc, the sibling ticket.
- **Work in the ticket's language** (fall back to the dev's language) —
  the dialog and your reports to the dev included, not only what lands in
  the ticket.

## Phase 0 — Intake

You need the **ticket** (an IID, a URL, a file reference like `T7` or a
slug — whatever the project's ticket source addresses tickets by). Fetch
it through that source; a reference resolving in no configured location is
a named failure, not a guess. Read title, description, acceptance
criteria, comments (earlier decisions live there), linked issues. Note
**which repos** the ticket touches: a change spanning backend and frontend
gets one plan whose tasks name their repo (`<repo>/path/to/module`),
because `implement` branches in each of them and a plan that hides a repo
produces half a branch — and the hidden one is rarely the second, more
often the third the ticket never mentions (the e2e repo whose specs the
change breaks).

**Completeness gate — does the ticket carry what a plan needs?** Four
inputs, checked one by one, not read past:

1. a goal you can state in one sentence,
2. acceptance criteria that are testable as written,
3. the parked dev questions **with** their answers — or the fact that none
   were parked,
4. the constraints the plan depends on: linked tickets, the design
   reference, and the delivery parts where the ticket names them.

Anything missing gets one line naming it *and* its bucket (PO flag, dev
question, clarification with the customer); then you plan with what is
there and carry the gap as a marked assumption — never as a stop.
**This is a gate, not a review:** you check that the inputs are present,
never whether their content is right. Where `refine-ticket`'s dev mode
ran, the gate normally comes out empty — that is the expected result, not
a reason to look harder.

If a plan from a previous run already exists in the ticket, say so and
ask: **update it or replace it?**

**Update mode has a procedure — follow it, don't improvise.** An old plan
is a claim about a codebase that has since moved:

1. **Verify its references first.** Every path, identifier, test and
   convention the plan names: does it still exist, still say that? Read;
   don't trust the plan's own wording.
2. **Correct only what you can evidence.** A step whose reference is gone
   is rewritten with the reason ("`FooService` was split in !412"); one you
   merely find unfamiliar stays. Silent modernization of a plan someone
   agreed to is the one thing update mode must not do.
3. **Check the claimed state of progress.** Ticked-off steps and "Stand"
   lines are claims: confirm them against the branch and the commits — a
   stale tick is what makes a resumed `implement` skip real work.
4. **Say what you changed and why**, one line per touched step.

## Phase 1 — Research (silent)

Read the code the ticket points at: the affected modules, their tests,
the patterns similar features follow, validation rules, states, error
paths. Check in-flight work (open MRs/branches touching the same area)
and linked tickets for constraints. Targeted reads — a handful of
well-chosen searches beats an inventory. Research is raw material: it
shapes the plan and the watch-outs, not a lecture.

**First-time plans get the same discipline as an update.** Steps 1 and 3
of *Update mode has a procedure* (Phase 0) are not update-only: the ticket
is a claim about the codebase too. Verify the references it names — paths,
identifiers, tests, every "X already exists" and every ticked criterion —
and **read; don't trust the wording**, the ticket's own as little as a
plan's. A grep that finds nothing proves one spelling absent, not the
thing missing: counter-check through the effect (the caller, the route
table, the test) before a "does not exist" becomes a premise of the plan.

## Phase 2 — Decision dialog

Only for what genuinely branches — either-or questions, not a decision
tree:

- **Approach** — when two implementations are defensible, present both
  in two lines each and recommend one. One question.
- **Order & cut** — where the work splits into independently testable
  parts, propose the cut through
  [../shared/ticket-split.md](../shared/ticket-split.md): evidence,
  verdict, then form — and expect Form C (one ticket, two parts, a seam
  in the implementation) more often than a spin-off at this point, since
  the ticket is already scoped. Where the ticket **already names its
  parts**, you don't re-cut it: carry the seam forward as the module says
  and group the task list by it.
- **Open ends** — anything the ticket leaves genuinely open that changes
  the plan (data migration yes/no, feature flag yes/no, …).

Most tickets need 1–4 questions; zero is a valid count. When the
branches are resolved: **"Is there anything we haven't covered that
could affect this plan?"**

**Quick mode:** on request ("just write the plan"), skip the dialog —
pick the recommended answer for every branch, mark each as an
assumption in the plan.

## Phase 3 — Deliverable

One fenced markdown block, ready for the ticket:

- **Task list** — GitLab task list (`- [ ]`), in build order, each step
  independently verifiable and naming the code area it touches
  (`path/to/module`). Where the ticket has delivery parts, one group per
  part with the seam between the groups.
  **The size test is a junior:** a task is right-sized when a developer
  new to this codebase could finish it without asking you anything — so
  it names what to touch, what the result must do, and how it is verified
  (the test, the command, the visible behavior). Apply it as a test, item
  by item: name the question a junior would still have to ask; if there is
  one, the task gets that answer written into it or is split. A step that
  hides three steps fails the test.
- **Watch-outs** — the traps: conventions to follow (with source),
  existing behavior not to break (with code reference), test targets,
  in-flight work to rebase on, marked assumptions, flags for the PO, and —
  as its own line where any exist — **clarifications with the customer**
  (the question plus who has to be asked).
- **Repos in scope** *(only where more than one)* — a **row per repo**, not
  one line: three repos with different base branches do not fit in a
  sentence, and `implement` reads this block instead of re-deriving any of
  it.

  | Repo | Base branch | Order | What it needs from the others |
  |---|---|---|---|
  | `<repo>` | `<the branch that exists **there**>` | `<1…n>` | `<consumed output, regeneration step, port>` |

  - **Base branch per repo, read in that repo** — never inherited from its
    neighbours. Two repos on `develop` and a third that has only `main` is
    the ordinary case, and the branch this row names is the branch
    `implement` branches from.
  - **The mechanics, not just the order.** The repo whose output another
    consumes goes first (the backend whose schema generates the frontend's
    client) — and the consuming row says what that costs: the regeneration
    command, that it runs against the run's **own slot** rather than the
    base port, whether the generated file lands as its own `chore:` commit
    or is discarded again. The order alone is the half that never broke.
  - **Delivery vocabulary follows the project**, from `workflow.md`'s
    `Push policy`: with `commit only` there are no MRs to order, and the
    plan says build order instead of promising merge requests the team
    does not use.
  - **Check for the *n*-th repo, not the second.** The repo that gets
    forgotten is the one the ticket never mentions — typically the e2e or
    test repo that breaks anyway. Name every repo the change reaches, and
    where you found no further one, say that you looked.

Then write it to the ticket as agreed and confirm with the link, or with
the **path** for a file ticket. Outside the block, one **what changed**
list where anything besides the plan was touched: acceptance criteria you
corrected (with the evidence), dev questions you checked off, un-ticked
plan steps. Close with the handover line: run `implement` on this ticket —
it will find the plan.
