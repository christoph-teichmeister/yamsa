# Shared module — feasibility check

Not a skill entry. This module is run *inside* another skill
(`create-ticket`, `refine-ticket`, `open-issues-analysis`) to answer one
question: **does this idea/ticket clash with what already exists?** The
calling skill decides what to do with the result; this module only
produces it.

## Inputs (provided by the caller)

1. **Subject(s)** — the idea, draft, or ticket(s) under check: raw text
   or issue reference(s).
2. **Scope** — the project's **open tickets**, wherever they live. The
   project's `## Ticket source` block (`.claude/beyonder/workflow.md`) says
   where and how to read them; the calling skill's access decides the
   mechanics: `glab`/`gh` for dev skills, the connected tracker MCP for
   chat skills, plain file reads for markdown ticket files (an `index:`
   entry, if the block names one, is the cheapest enumeration). On file
   tickets, "open" is not a field — derive it from the project's
   convention (status line, folder, index) and record which convention you
   used under `not-checked` if it had to be guessed. No reachable scope at
   all ⇒ every list is empty and `not-checked` says so; that is a valid
   result, not a failure.
3. Optional: **codebase access** — a repo checkout, or file reading
   through the tracker/host access. Without it, skip the codebase pass and
   report that.
4. **Mode** — `single` or `sweep` (below).

## Checks

Run against the scope, evidence-first — every hit quotes the overlapping
text and names its source (`#iid`, file, or doc):

1. **Duplicates** — an open issue already describes the same problem or
   the same change, whether or not the wording matches. Key-term search
   first, then read the candidates; judge by substance, not title.
2. **Overlaps** — an open issue touches the same feature area or screen
   so that building both independently would collide or double work.
3. **Contradictions** — an open issue demands what the subject rules out
   (or vice versa), or plans a change to the same behavior in a different
   direction. Quote both sides.
4. **Already exists / conflicts with current behavior** *(codebase pass,
   only with code access)* — the subject asks for something the product
   already does, or assumes current behavior that the code contradicts.

## Modes

- **`single`** (create-ticket, refine-ticket): one subject against the
  scope. Quick — minutes, not a backlog audit: key-term searches plus
  reading the plausible candidates. Classify each hit as **strong**
  (plainly the same problem/feature — the caller should surface it
  before doing more work) or **weak** (worth a line in the wrap-up).
- **`sweep`** (backlog check): every open issue against every other.
  Thorough but proportionate: cluster by feature area first, then check
  within and across clusters; don't force a verdict on every pair. No
  strong/weak split — everything is a candidate for the caller's report.

## Result contract

Return to the calling skill (not to the user) a structured result:

```
duplicates:      [{subject, match, quote both sides}]
overlaps:        [{subject, match, quote, what collides}]
contradictions:  [{subject, match, quote both sides, proposed resolution}]
already-exists:  [{subject, evidence from code/product, quote}]   # only with code access
not-checked:     [what was skipped and why]                        # e.g. no code access
```

In `single` mode every entry additionally carries its `strength`
(strong/weak, per the mode's classification); `sweep` mode has none.

Empty lists are a valid result. All findings are *candidates* — the
verdict belongs to the user, surfaced by the calling skill in its own
format and language.
