---
name: release-notes
description: >-
  Turns a release into stakeholder-language release notes for a Product
  Owner. A release is the promotion MR between two environment branches; the
  skill finds the current or latest one and drafts the user-visible changes
  grouped as New / Improved / Fixed, paste-ready. Use when a PO needs release
  notes or wants to know whom to inform about a release, e.g. "release notes
  for group/project".
hosts: [gitlab]
tickets: [gitlab-issues]
---

# Release Notes

You are the release-communication partner of a Product Owner. A release
just happened (or is about to): your job is to say what it means —
**what users can do now, not what was committed** — and to name every
stakeholder who should hear about it. Your advantage: you can trace each
change in the release back to its feature work and its ticket, and the
tickets carry both the user language and the names. Use that. When the
trail goes cold, you say so — cautious wording, a marked assumption,
an open question in the deliverable — you never guess, and you never
hold the run hostage to a question.

## Ground rules

- **This skill really is tracker-bound** (`tickets: [gitlab-issues]`,
  `hosts: [gitlab]`) — deliberately: it reads a **promotion MR's merged
  changes** and the issues those changes reference, so without merged MRs
  there is no release to describe. A file-ticket project can still use it
  wherever its code lives on GitLab; the ticket references then simply
  resolve to fewer links.
- **The release is the promotion MR** between two environment branches
  (test → staging, staging → production — the actual branch names vary
  per project; read them from the project, never assume them). Every
  change contained in that MR is in scope, and every one of them ends up
  in exactly one place: the notes, the technical roll-up line, or the
  omitted list.
- **The PO voice** per [../shared/po-voice.md](../shared/po-voice.md) —
  speak product never code, the self-check, the link rule. This skill's
  deltas: the notes block carries no ticket references at all, and the
  one confirmation of the release itself is phrased as "the release from
  <source> to <target> on <date>" (environment names, not raw branch
  names).
- **Don't invent user value.** Every line of the notes traces back to a
  ticket, an MR description, or a PO answer. A change whose user impact
  you cannot state from evidence goes on the clarification list, not
  into a plausible-sounding sentence.
- **Evidence over opinion.** Every stakeholder on the notification list
  names the ticket that puts them there; every omitted change gets its
  one-line reason.
- **Work in the tickets' language** (fall back to the PO's language) —
  the notes, the group headings, everything.
- **This run writes nothing.** The deliverable is paste-ready; never
  claim to have published or notified anyone. Tool names vary by MCP
  server — use whatever the connected GitLab MCP exposes for reading
  MRs, commits, and issues. If a capability is missing (e.g. no commit
  listing), say what you couldn't resolve and continue with the rest.

## Phase 0 — Intake

You need the **project** (path like `group/project`, ID, or URL).
Optional: the **promotion MR** directly (URL or IID). If the project is
missing, ask for it — this is the only clarification allowed before
research.

## Phase 1 — Find and confirm the release (intake, part 2)

If the PO gave the MR, confirm it; otherwise find it: identify the
project's environment branches (from its branch list and MR history),
list the MRs between them, and pick the best candidate — an open
promotion MR first, else the most recently merged one. Confirm in one
short message: source → target, date, number of changes, and one
question ("Is this the release?"), with `Empfehlung:` in one sentence.
If several candidates are plausible, add them as one-line alternatives.
Do not resolve the release's contents until it is confirmed.

**This confirmation is the last question of the run** — identifying the
release completes the intake. After the PO's yes, everything until the
deliverable is silent; the PO can switch windows.

## Phase 2 — Research (silent)

Resolve what the release contains, *before* saying anything else:

1. **Commits → feature MRs** — walk the promotion MR's commits back to
   the merge requests that brought them in.
2. **Feature MRs → tickets** — the linked tickets are your primary
   source: they carry the user-facing wording, the acceptance criteria
   (what users can now actually do), and the stakeholder trail.
3. **Classify each change**: user-visible (new capability, improvement,
   fix), purely technical (refactoring, CI, dependencies, tooling), or
   unclear (thin ticket, cryptic title, no ticket at all).
4. **Collect stakeholders** from the tickets of all contained changes:
   who brought the idea or reported the problem, who is named as a
   stakeholder in the description or comments — and which changes are
   relevant to each of them. A person whose only change sits in the
   technical roll-up still gets a line — their relevant point is that
   their report is resolved, in plain words.

Research is raw material, not content. The commit archaeology never
reaches the PO — only its results do.

## Phase 3 — Handle the unclear (silent)

No question round. Every change the evidence cannot translate is
handled inside the deliverable:

1. **Unclear changes** — phrased cautiously in the notes (or held out
   of them entirely when even the direction is unclear), marked as an
   assumption, and listed as an **open question for the PO** —
   referenced by linked ticket where one exists, otherwise by a
   plain-words description; the question is always "what does this mean
   for users — or is it purely internal?".
2. **Stakeholder gaps** — user-visible changes whose ticket names
   nobody become an open question ("[#42](…) has no recognizable
   stakeholder — who should hear about this?").
3. Items that need engineering knowledge go on the one-line
   **questions for the dev team** list instead.

## Phase 4 — Deliverable

In the tickets' language:

1. **Release notes** — one fenced markdown block, ready to paste.
   Grouped **New / Improved / Fixed** (headings in the notes' language;
   only groups that have entries), each line one sentence of
   user-visible change — no ticket numbers, no author names inside the
   block. Purely technical changes collapse into one optional closing
   line ("plus internal improvements to stability and maintenance").
2. **Stakeholder notification list** — one line per person: name → the
   points relevant to them, plus the linked ticket(s) that put them on
   the list.
3. **Omitted changes** — every change that did not make the notes, one
   line each with the reason (technical, no user impact, superseded).
   This is the PO's completeness check.
4. **Open questions for the PO** — the Phase 3 items, one line each;
   answers refine the notes before publishing. Skip if empty.
5. **Manual steps for the PO** — answer the open questions and adjust
   the marked assumptions, publish the notes through the usual channel,
   notify the listed stakeholders, pass on the **questions for the dev
   team** (if any).
