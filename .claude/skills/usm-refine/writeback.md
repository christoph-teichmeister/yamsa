# Module: write-back of agreed changes

Used by `usm-refine`. Governs how a change the PO agreed to actually
reaches the map. Exactly one of two modes is active per session; the
skill announces the mode once (at the first write) and states it again
in the deliverable.

## Mode selection

- **Direct mode** — the board was read via MCP **and** write tools are
  available. Don't probe with test items: attempt the first real agreed
  change; if it fails with a permission error, announce the switch to
  changeset mode in one line and continue there. Changes already applied
  stay applied and appear in the change log.
- **Changeset mode** — everything else: board came from export/paste,
  MCP is read-only, or writes failed. Every agreed change is recorded as
  an operation in the changeset (format below).

Never mix silently. Never claim a write that didn't happen.

## Direct mode rules

- Write **only** what the PO just agreed to — one finding, one write,
  one one-line confirmation with the deep link. No batching, no
  "while I'm at it" cleanups.
- Match the board's conventions from the legend: new stories get the
  color/shape/position an existing story in that activity and slice has.
- Deletions: prefer moving the card to a clearly labeled parking area
  (`usm-refine: removed <date>`, written in the board's language) over
  destroying it, unless the PO explicitly wants it gone.
- If a single write fails mid-session, retry once; then record that one
  operation in a (now mixed-deliverable) changeset and say so — the
  change log marks it "not applied, in changeset".

## Changeset mode: the handover format

The changeset is a **self-contained fenced markdown block** — the PO
hands it to a colleague whose Claude session has Miro MCP access; that
session applies it without needing any context from this conversation.
Deliver it in the Phase-4 deliverable, and mid-session whenever the PO
asks.

Structure — headings, labels, and instructions in the **board's
language** (fall back to the PO's), like every other deliverable; the
English wording below is the reference, not a fixed string:

```markdown
# Changeset: <board name/url> — <date>
<n> operations. Agreed in the usm-refine session with <PO>.

**How to apply:** hand this complete block to a Claude session with Miro
MCP access to this board and say: "Apply this changeset." The rules for
whoever applies it are at the end of the block.

## Op 1 — UPDATE
- Target: "<exact current card text>"
  (activity <A>, column <S>, slice <MVP>) <widget URL if known>
- New text: "<complete new text>"
- Reason: <one sentence>

## Op 2 — CREATE
- New story: "<text>"
- Position: activity <A>, column <S>, slice <R2>, below "<neighbor card>"
- Format: like the existing stories there (color/shape per the legend)

## Op 3 — MOVE / DELETE analogously:
- MOVE: target + from → to
- DELETE: target + reason; move the card to the parking area instead of
  deleting it, unless this block explicitly says "delete permanently"

## Rules for whoever applies this
1. Read the board first and locate every target unambiguously.
2. Target not found, or found more than once → skip the op, don't guess.
3. Execute only the listed ops, change nothing else on the board.
4. Return a result table at the end: op / applied | skipped (reason).
```

Targeting rules when writing operations:

- **Widget URL/ID if known** (MCP read worked but writes don't) — the
  strongest anchor, always include it.
- **Otherwise text + location**: the exact, complete current card text
  in quotes plus activity/column/slice. If the text is not unique on
  the board, add a disambiguator ("the lower of the two").
- New text is always the **full replacement text**, never a diff
  ("change X to Y" invites paraphrasing).

## Linked tickets outside Miro

If map cards link to tickets in an external system (e.g. GitLab) and
the PO agrees to update one: same two modes — write via that system's
MCP/CLI when available and writable, otherwise a paste-ready block per
ticket appended after the changeset. State which happened.
