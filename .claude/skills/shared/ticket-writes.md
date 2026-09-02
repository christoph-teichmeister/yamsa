# Shared module — reading and writing tickets

Not a skill entry. This module is the single source for **how a ticket is
found, and how a write into one stays safe** — the rules every
ticket-touching skill (`implement`, `technical-planning`, `create-ticket`,
`refine-ticket`, `po-review`, `design-check`, `open-issues-analysis`)
follows instead of restating. A consumer restates only what it *changes*;
everything below binds as written.

## Ticket access follows the project, not a platform

A ticket is its **content**: an issue in a tracker and a markdown file in
a `Tickets/` directory are equally first-class. Where the project's
**`## Ticket source`** block is reachable (`.claude/beyonder/workflow.md`,
written by `beyonder-setup`), it is the authority on where tickets live,
how they are addressed, and how to read and write them back:

- **Resolve every reference through it, top to bottom.** A reference
  matching no configured location is a **named failure**, never a guess —
  a wrong ticket silently used is worse than a stop.
- **Honor its anchored paths.** File locations are written as `<root>/…`
  or `<repo>/…` and resolved from git, not from the caller's working
  directory — half the reads happen from a worktree, where a bare
  `../Tickets/` lands somewhere that does not exist.
- **Not reachable?** In a chat session without the repo: ask once at
  intake whether this is a tracker project or a file-ticket project, and
  where, then keep the answer for the session. In a checked-out project:
  look for a tracker on the repo's remote, then the common ticket
  directories, and record what was used as a marked assumption.

**Reaching a tracker.** In a checked-out dev context the dev's personal
binding decides the path — the `## Access` section of
`.claude/beyonder/access.local.md` (contract: `config-discovery.md`,
§ *Access bindings*): the bound tool and only that tool, refusal with the
setup fix line when the file is missing. In a chat product the connected
tracker MCP is the path, and tool names vary by server — use what it
exposes, degrade gracefully where a capability is missing. File locations
are read with the file tools and written with an edit in every context.

## Show before write

- **Nothing is written whose content the user has not seen.** The
  deliverable is shown as a fenced block, then one confirmation question,
  then the write. A permissive-sounding earlier message ("leg das einfach
  an", "mach das fertig") authorizes the *task*, never a write of unseen
  content. (Autonomous skills substitute their own sanctioned moment —
  `implement`'s intake confirmation covers its continuous bookkeeping
  writes — but never skip the principle for content-shaping writes.)
- **Confirm each write in one line** — with the link on a tracker, with
  the **path** on a file ticket.
- **Never claim a write that didn't happen.** A missing capability or a
  403 means: say so in one line, deliver the content paste-ready, move
  on. The paste-ready block is a first-class outcome, not an apology.

## The fence trap (file tickets)

The fenced block you showed is **presentation, not payload**. Write its
content, never its outer fence — and keep any fences *inside* the content
intact (use a longer outer fence where you must nest). A ticket file with
a stray ``` renders everything after it as one code block.

## Snapshot rule (unversioned file tickets)

A ticket file outside version control has no history — an edit is the
only version left. So, before the **first** write of a session:

1. **Check for an existing snapshot first.** A snapshot from today, per
   the governing convention, is this session's snapshot — never write a
   second one.
2. **Copy the file once**, next to itself, as
   `<name>.<YYYY-MM-DD>.bak.md`, and name that path in the write
   confirmation.
3. **The project's own convention wins.** Where the `## Ticket source`
   block names another snapshot convention (e.g. one copy of the whole
   ticket directory into `<root>/tmp/`, no new files inside the ticket
   directory), that replaces this default wholesale and is followed as
   written — the project's word beats this module's default. No
   convention named ⇒ the copy above is the rule, not a suggestion.

Snapshots older than ~30 days can be deleted; say that once instead of
growing a graveyard. A **versioned** ticket file needs no snapshot (`git`
is the snapshot), and a **newly created** file has nothing to lose yet —
only edits to an existing unversioned file snapshot first.
