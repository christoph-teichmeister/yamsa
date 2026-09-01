# GitHub mechanics for mr-review

The GitHub counterpart to gitlab.md. `<pr>` = PR number, `<owner>/<repo>`
from config/`gh repo view`. Posting identity is the invoker's `gh` auth
(`GH_TOKEN` overrides it if the config names a token env var).

## Reading

```bash
gh pr view <pr> --json title,body,headRefName,baseRefName,headRefOid,author,url
gh pr diff <pr>                              # the diff
gh api "repos/<owner>/<repo>/pulls/<pr>/comments" --paginate   # review (diff) comments
gh api "repos/<owner>/<repo>/issues/<pr>/comments" --paginate  # plain comments
# threads incl. isResolved — only via GraphQL:
gh api graphql -f query='query($owner:String!,$repo:String!,$pr:Int!){
  repository(owner:$owner,name:$repo){pullRequest(number:$pr){
    reviewThreads(first:100){nodes{id isResolved comments(first:50){
      nodes{id databaseId author{login} body path line}}}
      pageInfo{hasNextPage endCursor}}}}}' \
  -f owner=<owner> -f repo=<repo> -F pr=<pr>
```

Build the two indexes (discussed topics, own unresolved threads) from
`reviewThreads`; identify own threads by author login or the marker footer.

## Positioned diff comments (one thread per finding)

```bash
gh api -X POST "repos/<owner>/<repo>/pulls/<pr>/comments" \
  -f body=@<file with markdown body> \
  -f commit_id=<headRefOid> \
  -f path=<file path in PR branch> \
  -F line=<line in the new file> \
  -f side=RIGHT
```

- Added/changed line → `side=RIGHT` + new-file line number.
- Deleted line → `side=LEFT` + old-file line number.
- Multi-line finding → add `start_line` + `start_side`.
- GitHub rejects lines outside the diff (`422 Validation Failed`) → fall
  back to a plain issue comment quoting `file:line` — never drop the
  finding silently.

` ```suggestion ` blocks work exactly like on GitLab (replace the commented
line range, one-click apply) — but there is no `:-A+B` extension; use
`start_line` to widen the range instead.

## Replying and resolving

```bash
# reply inside an existing thread
gh api -X POST "repos/<owner>/<repo>/pulls/<pr>/comments/<comment_id>/replies" \
  -f body=<markdown>

# resolve a thread — GraphQL only, needs the thread node id (see Reading)
gh api graphql -f query='mutation($id:ID!){
  resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' \
  -f id=<thread_node_id>
```

## Screenshots — no upload API

GitHub has **no public API to upload images into PR comments** (the web
UI's `user-images` upload path is not exposed). Do NOT try workarounds
(committing images to branches, release assets). Instead:

- Put the full walkthrough with images into the **local report** — the
  entry skill's report file under `.claude/beyonder/reviews/`
  (`mr-<pr>.md` for reviews, `mr-<pr>-walkthrough.md` for standalone
  walkthroughs), next to its screenshots — and keep the report + images
  instead of deleting them in cleanup.
- In the PR summary comment, render the walkthrough as text steps and
  reference the report: "Screenshots: see the local review report."
  (canonical English — render it in the configured language).

## Description and summary comment

```bash
gh pr edit <pr> --body "<markdown>"          # set description
gh api -X POST "repos/<owner>/<repo>/issues/<pr>/comments" \
  -f body=@<file>                            # summary comment (no position)
```

## Marker footer

Same rule as GitLab: posting as the invoker appends to **every** comment
(in the configured review language):

```
---
🤖 *Automated via `/<invoking skill>` (Claude Code)*
```

(`<invoking skill>` = the entry skill of this run: `mr-review`,
`content-review`, or `walkthrough`.)
