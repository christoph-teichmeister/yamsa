# Describe module — MR description & change listing

Not a skill entry. Internal module of `mr-review`, run as its Phase 2:
nobody describes an MR in this workflow without reviewing it, so there is
no standalone entry and no describe mode.

Both artifacts here are drafted by **one mechanical-tier subagent**
working from the manifest, the patch directory, and the ticket — you
review its output, you don't read the diff yourself.

## Description

If the MR description is empty or trivially short (< ~2 sentences), have
the subagent draft one: what the change does, why (from the ticket if
any), scope of the diff, anything reviewers should know. Sanity-check the
draft, then update via `glab mr update <iid> -d "..."` (a platform
write — may prompt). **Never overwrite an existing meaningful
description.** A meaningful description already there ⇒ no draft at all;
rewriting what the author wrote is not this module's business.

## Change listing

Only if the config's Comments section says change listing: yes.

The same subagent produces the structured listing: grouped by area,
file(s) — what changed, one line each; noise and formatting-only files as
one collective line per group.

## Output

The listing opens the summary (remote) or the report (local); don't post
it as a separate note. The description update is the only write of this
module, and only under the rules above.
