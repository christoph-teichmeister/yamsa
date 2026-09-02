---
name: figma
description: >-
  Foundation skill for working with Figma designs through the Figma MCP:
  resolves any Figma link, maps a big file into a reusable node map, and
  drills down to small nodes for exact design values — colors, spacing,
  typography. Building block for design-check, content-review and implement.
  Use when exact design data is needed from Figma, e.g. "get the button
  styles from <figma url>".
user-invocable: false
hosts: any
tickets: none
---

# Figma

You are the layer between a Figma file and whoever needs facts from it —
a skill verifying designs against ACs, an implementation matching a
design, a dev asking for the spacing of one component. Your job: get the
**exact** design data with the fewest, smallest MCP calls, and never
make anyone link frames one by one.

Your advantage: done right, one drill-down maps a whole file and every
later question is a cheap, precise lookup. Done wrong, one oversized
call overflows the context. You do it right.

## Ground rules

- **Never eyeball a value.** Colors, spacing, font sizes/weights, radii,
  exact copy — always from the MCP's design data on the smallest node
  that contains them. Screenshots are for orientation and evidence,
  never for measuring.
- **Small nodes only.** Metadata/structure calls on a whole page or a
  huge frame overflow — descend: shallow structure first (depth ≤ 2),
  then targeted calls on the small nodes you actually need. If a
  response is still too large, dump it to a file in `tmp/` and filter.
- **Map once, reuse forever.** For any file you'll touch more than once
  in a session, build the node map (below) first and work from it.
- **Tool names vary by MCP server.** Use whatever the connected Figma
  MCP exposes for structure/metadata, design context/variables, and
  screenshots. A missing capability is named and worked around (e.g. no
  variables API ⇒ resolved values from the node data); no Figma access
  at all ⇒ say what's missing (login? MCP config? → `beyonder-setup`
  checks both) and stop — there is no eyeball fallback.
- **Facts carry their source.** Every value you hand over names its
  node (id + name), so it can be re-checked and deep-linked.

## Phase 0 — Intake

You need a **Figma link** (any form — file, page, frame, or node URL;
extract file key and node id) and **what is needed** from it (from the
calling skill or the user). A file link without a node is fine — that's
what the map is for. Ask only if both the link and the need are missing.

## Phase 1 — Node map

Skip if the need is a single known node. Otherwise, do the drill-down
**once**:

1. Fetch the file/page structure shallowly (depth ≤ 2).
2. Write the map — default `tmp/figma-map-<file-key>.md`, or the
   target path the calling skill names: a table of section/frame node
   ids, names, and what each shows (one line each), plus the file key
   and the URL pattern for deep links.
3. Reuse an existing map from the same session instead of re-fetching;
   append newly discovered nodes to it.

The map is the answer to "which frame is X?" for the rest of the
session — calling skills get its path instead of raw structure dumps.

## Phase 2 — Extraction

For each thing needed: find its node via the map, then pull the design
data on that node (descending further if it's still composite). Collect:

- **Values** — exact tokens/styles as the file defines them (variable
  name when one is bound, resolved value always).
- **Content** — exact copy, states present (hover, empty, error,
  disabled — say which exist and which don't).
- **Orientation screenshot** of the node when the caller needs visual
  evidence — clearly labeled as orientation, not as a measurement.

## Deliverable

Structured, terse, source-annotated — a table or list of
`what · value · node (id, name) · deep link`, plus the node-map path
for follow-ups. When a needed state or frame **does not exist** in the
file, that is a first-class finding ("no error state for X anywhere in
the file"), not a silent gap — for `design-check` it is the product.

## As a building block

Calling skills (`design-check`, `content-review`'s design axis,
`implement` collection mode) invoke this flow with
their link and their need, and
consume the deliverable — typically via a subagent when the extraction
is large, keeping the raw Figma responses out of the caller's context.
The node map file is the shared artifact between them.
