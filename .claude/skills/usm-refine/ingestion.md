# Module: board ingestion from Miro

Used by `usm-refine`. Goal: turn a Miro board into a faithful structured
model of the User Story Map **plus** an inventory of the supporting
artifacts around it — **before** any analysis. Everything here is silent
background work except the final playback.

Validated against real boards via the Miro MCP on 2026-07-27; the traps
below were actually observed, not hypothesized.

## Read the board

Tool names vary by Miro MCP version; use whatever it exposes for reading
items with coordinates (e.g. `layout_read`, `board_list_items`,
`context_explore`). The pattern that works:

1. **Board scope first.** A board-level read returns only frames and
   top-level items — no frame children. Collect the frame list.
2. **Then one read per frame** (`?moveToWidget=<frame_id>`) to get its
   children: text, x/y, width/height, color, shape, item type, and the
   item's own widget URL. Keep those URLs — they become deep links in
   findings, writes, and the deliverable.
3. **Fetch item details where the type has them.** Cards can carry
   descriptions, fields, and assignees beyond the visible title — the
   third analysis pass runs against exactly this detail level, so a
   title-only read silently skips a whole pass. If details are
   inaccessible, say so.
4. Note any "skipped unsupported items" counts. A few are normal
   (images, reactions); a large number means content you cannot see —
   say so.

**Coordinate trap:** child coordinates are frame-relative, not absolute.
Two stickies in different frames can report identical x/y. Convert to
absolute positions (frame position + child offset) before any
cross-frame geometry, or reason strictly within one frame.

## Identify the artifacts

The USM is rarely alone on the board. Before reconstructing the map,
classify what each frame (or floating cluster) is:

- **The USM itself** — the grid of backbone + columns + story rows.
  If several map-like frames exist (old version, playground copy), ask
  the PO which one is authoritative — one question, in the playback.
- **Legend** — color/shape key. Read it first; it defines what colors,
  shapes, and rows mean on *this* board. Never assume the conventions
  of the last board you saw.
- **Supporting artifacts** — personas, notes/parking lot, goals,
  design screenshots or links, open-question stickies. These are
  **context sources for pass 2**, not map items: inventory them (what,
  where, one-line gist) but keep them out of the map model.
- **Noise** — decoration, templates, empty frames. Ignore, but count.

## Reconstruct the map structure

Real boards rarely connect anything: activity headlines float in their
own frames, stories sit in a separate body frame, and no connectors
exist. The structure lives in the geometry — recover it mechanically:

1. **Backbone (activities):** the top row — typically the largest
   shapes, a distinct color, or one frame per activity. Order by x.
2. **Columns (tasks/steps):** cluster the x-centers of cards below the
   backbone. Within-column spacing is small and regular; between-group
   gaps are several times larger. Map each cluster to the backbone item
   it horizontally overlaps (nearest center if ambiguous).
3. **Rows (priority / release slices):** cluster y-positions.
   Cross-check against sticky colors if the legend assigns meaning to
   them.
4. **Release cuts:** **trap — cut lines can be invisible.** A dashed
   "MVP cut" line may come through only as two tiny endpoint dots plus
   a text label, or not at all. Treat any horizontal text like "MVP",
   "Release", "Cut", "Phase", "Wave" between rows as a slice boundary
   candidate — and always confirm detected slices with the PO.
5. **Estimates (T-shirt sizes / SP):** look in sticky text suffixes
   ("(M)", "5 SP"), small overlapping stickies, or card fields. Miro
   *tags* may not survive into the API view at all — if the PO expects
   estimates and you find none, say exactly that and ask where they are
   recorded instead of concluding there are none. Estimates are
   read-only facts; the only thing `usm-refine` ever does with them is
   an estimate-recheck flag.

Result: an inventory where every card has — widget URL, text, details
(if any), activity, column, slice, color, estimate (if any) — plus the
artifact inventory. This model, not the raw dump, is what the skill
works with.

## Playback (mandatory, before any analysis)

A misread map poisons every downstream finding. Play the skeleton back
to the PO and get a confirmation:

- One line per activity: name + column count + story count.
- One line for the slices: names/labels and how many stories each holds.
- One line for the supporting artifacts found ("3 Personas, 1 Legende,
  1 Notiz-Frame").
- Up to 3 open ambiguities as direct questions (e.g. "I see a possible
  release cut between row 1 and 2 — correct?"). No more than 3; park
  the rest for the findings dialog.

Hard cap: 10 lines + the questions. Do not list stories here. Wait for
the PO's confirmation before analyzing.

## Fallback: no MCP access to the board

Seen in practice: Miro OAuth is **team-scoped**, app installation may be
admin-restricted, and **guests cannot connect at all** — API access
follows team membership, not board shares. If reads fail with permission
errors:

1. Ask the PO to re-authenticate and pick the right team in the consent
   dialog (if they are a member and the app is approved).
2. If they are only a guest on the board's team: ask them to copy the
   board (select all → copy → paste into a new board in a team where the
   MCP works), or
3. Take a **CSV/text export or paste** instead. Then ask for the
   structure the geometry would have given you: "List the activities
   left to right; for each, its columns; for each column, the stories
   top to bottom; where are the release cuts? What else is on the board
   (personas, notes)?" — the PO answers once, you build the same
   inventory (without deep links) and continue normally.

No MCP read also means no MCP write: [writeback.md](writeback.md) runs
in **changeset mode**. Never silently degrade: state which path you are
on and what is missing (e.g. "no deep links — board was pasted, not
read; changes go into a handover changeset").
