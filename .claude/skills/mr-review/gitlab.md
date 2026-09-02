# GitLab mechanics for mr-review

All examples assume `<id>` = URL-encoded project path or numeric ID and
`<iid>` = MR IID. When posting as the bot, prefix the command with
`GITLAB_TOKEN=$REVIEW_BOT_TOKEN` — that env var name is canonical
(core.md Preflight); a bot posts only when it is exported.

## Reading

```bash
glab mr view <iid> --output json          # metadata incl. diff_refs, description
glab mr diff <iid>                        # the diff
glab api "projects/<id>/merge_requests/<iid>/discussions?per_page=100&page=1"
```

Discussions are paginated — follow pages until empty. Each discussion has
`id`, `notes[]` (with `author`, `body`, `position`), and `resolved` on
resolvable notes.

## Positioned diff discussions (one thread per finding)

Positions require the MR's `diff_refs` (`base_sha`, `start_sha`, `head_sha`)
from `glab mr view --output json`.

⚠️ **Do NOT use `glab api -f "position[...]=..."` for this call.** glab puts
the bracketed keys literally into a JSON body; GitLab silently ignores the
unknown keys and creates a plain (unpositioned) `DiscussionNote` instead of a
`DiffNote` — the thread then shows no file/line in the MR. Use curl with
form encoding, authenticated with the same token you post with:
`$REVIEW_BOT_TOKEN` if exported, otherwise the invoker's glab token
(`glab config get token -h <host>`; never print the token):

```bash
curl -s -X POST -H "PRIVATE-TOKEN: $TOKEN" \
  --data-urlencode "body@<file with the markdown body>" \
  --data-urlencode "position[position_type]=text" \
  --data-urlencode "position[base_sha]=<base_sha>" \
  --data-urlencode "position[start_sha]=<start_sha>" \
  --data-urlencode "position[head_sha]=<head_sha>" \
  --data-urlencode "position[new_path]=<file path in MR branch>" \
  --data-urlencode "position[new_line]=<line number in the new file>" \
  "https://<host>/api/v4/projects/<id>/merge_requests/<iid>/discussions"
```

**Verify the response**: the created note must have `"type": "DiffNote"` and a
non-null `position`. A `DiscussionNote` means the position was dropped —
delete the note and repost, don't leave it unpositioned.

- Added/changed line → `new_path` + `new_line`.
- Deleted line → `old_path` + `old_line` instead.
- Unchanged (context) line → provide **both** old and new path/line.
- If GitLab rejects the position (line not part of the diff), fall back to an
  unpositioned discussion quoting `file:line` in the body — never drop the
  finding silently.

## Conventional comment body

```
**issue (breaking):** <one-line subject>

<explanation: why it matters, concrete failure scenario>

```suggestion:-0+0
<replacement for the commented line(s)>
```
```

Labels come from the config's Comments section (default: `issue`,
`suggestion`, `question`, `nitpick`). The ` ```suggestion:-A+B ` block replaces A lines above
through B lines below the commented line — the author applies it with one
click. Only include one when the fix genuinely fits those lines; otherwise
describe the fix in prose.

## Replying and resolving

```bash
# reply to an existing discussion
glab api -X POST "projects/<id>/merge_requests/<iid>/discussions/<did>/notes" \
  -f "body=<markdown>"

# resolve a discussion (after the confirming reply)
glab api -X PUT "projects/<id>/merge_requests/<iid>/discussions/<did>" \
  -F "resolved=true"
```

## Screenshot upload

```bash
glab api -X POST "projects/<id>/uploads" -F "file=@<path>.png"
```

The response contains a `markdown` field (`![...](/uploads/...)`) — embed that
string directly in the summary note. If `glab api` refuses the multipart
upload, fall back to curl:

```bash
curl -s -H "PRIVATE-TOKEN: $TOKEN" \
  -F "file=@<path>.png" "https://<host>/api/v4/projects/<id>/uploads"
```

(`$TOKEN` as above: the bot token if exported, otherwise the invoker's
glab token.)

## Description and summary note

```bash
glab mr update <iid> -d "<markdown>"                 # set description
glab api -X POST "projects/<id>/merge_requests/<iid>/notes" \
  -f "body=<markdown>"                               # summary note (no position)
```

## Marker footer

When posting as the invoker (no bot token), append to **every** note (in
the configured review language):

```
---
🤖 *Automated via `/<invoking skill>` (Claude Code)*
```

(`<invoking skill>` = the entry skill of this run: `mr-review`,
`content-review`, or `walkthrough`.)

When posting as the bot, the footer is still appended to the summary note for
transparency, but may be omitted on individual finding threads.
