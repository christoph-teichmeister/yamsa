# Walkthrough module — feature documentation with screenshots

Not a skill entry. This module **documents a feature as it currently is**,
so reviewers and non-devs can see it without pulling the branch: steps,
screenshots, the flow end to end. Used by `/walkthrough` (its whole
deliverable) and as `mr-review`'s last phase, behind that skill's gate.

**One mode: documentation.** This module carries no verdicts, no
findings, no confidence filter, and no ACs-as-criteria — verifying that a
change is correct is [content-checks.md](../shared/content-checks.md)'s
job, reviewing the code is
[review-passes.md](../shared/review-passes.md)'s. Callers that want
judgment run those; nobody gets judgment from here.

**When it runs.** Only if the diff affects UI — a walkthrough of nothing
is a fabrication. No UI effect at all ⇒ say exactly that and stop; that
is a valid, honest result. Whether a caller runs the walkthrough at all
(`mr-review` gates it on the content review's verdict) is the caller's
decision, made before this module starts.

## Abort on the first problem — never a half walkthrough

**Any problem ends the walkthrough.** Not just broken tooling: a missing
browser tool, a dead or unreachable environment, rejected credentials, a
step that errors, a page that 404s, a state you cannot produce, a promised
visible behavior that does not appear, an exception in the console that
breaks the flow — all of them stop the run at that point.

**The deliverable then is the problem, and only the problem**: which flow,
which step, what you expected from it, what happened instead, one
screenshot of the failure state, and — where it was a configured fact
that failed — the exact config entry to fix (stale-config rule). The steps
that worked before it are **not** published: a walkthrough is a document
people rely on, and a partial one silently claims the feature is what it
shows. Keep the artifacts on disk; narrate only the abort.

Do not retry variations, work around the problem, or reroute to a
different flow to salvage a walkthrough. Do not turn the problem into a
finding with a verdict — that is a review, and this module doesn't do
reviews. Report it and stop; the caller decides what it means.

## What to walk

The configured **Flows** the diff touches (config's Flows section). Flows
is `-` and a ticket was fetched ⇒ follow the ticket's acceptance criteria
as a **route through the feature**, not as criteria: they describe what
the feature does, which is exactly what a walkthrough shows. Neither
available ⇒ walk the user-visible entry points the diff changes, per the
manifest.

**An empty state is not the end of the walkthrough.** If the seed data
doesn't exercise the changed feature, create the test data through the
feature's own UI — creating data is itself part of the flow being
documented. Then show the full loop against it: save, reload, the derived
values. (A state you cannot produce is a problem ⇒ abort.)

For visual changes to existing pages, capture the target branch state too
(before/after) — best effort; failing to get the "before" is not a
problem in the above sense, it is one missing image.

## Browser, artifacts, checkpointing

The mechanics are shared — read
[../shared/browser-discipline.md](../shared/browser-discipline.md) and
[content-checks.md](../shared/content-checks.md) § *Browser discipline &
screenshot checkpointing*, and apply them with the caller's `<run-tag>`
(`mr-<iid>` from `mr-review`; from `walkthrough` the tag of its object —
`mr-<iid>`, `t-<id>` or the sanitized branch name) and session
`-s=<run-tag>`: named
session bound to the run, the lock convention on a
singleton browser, artifact directory `<scratchpad>/<run-tag>-artifacts/`
outside the worktree, and **every artifact to disk the moment it is
captured**. Name screenshots `NN-<step>.png` in walk order.

NEVER write artifacts into the project working directory; if a tool drops
files elsewhere by default, point it at the artifact directory or move
them there immediately. That includes the browser CLI's own
`.playwright-cli/`: a screenshot the walkthrough publishes must not sit in
a directory the SessionEnd hook ages out.

## Environment

1. Environment per `.claude/beyonder/environment.md`. A `user-owned`
   server is verified up via the configured check and serving the walked
   branch; a `review-owned` one you start yourself — run the `setup` steps
   (substituting placeholders like `<iid>`), apply the `Data` policy
   (fixtures/dump into a scratch DB, current state, or reset per config),
   then `serve` on the configured port/base URL. Never mutate the dev's
   real DB with this branch's migrations. The `teardown` steps are a debt
   you owe the caller's cleanup, even after an abort.
2. Log in with the credentials from config (resolve `env:` tags from the
   environment; a `create-admin:` entry means run that command against the
   walkthrough DB first, then log in with the account it creates). A
   walkthrough shows the feature, so the account is whichever one can
   *see* it — proving permission gates with least privilege belongs to
   `content-review`.
3. Walk the flows, screenshotting each meaningful step.
4. Shut down whatever you started.

Any failure in steps 1–3 is a problem per the abort rule.

## Output

A **"Feature walkthrough"** section: step description + image, in walk
order, in the configured language. No verdicts, no severity labels, no
recommendations — what the feature does and what it looks like.

Where it lands is the caller's business (own note on the MR, a comment on
the ticket, embedded in a review summary, or a local report with
relative-linked screenshots); this module
produces the section and names the artifact paths. On GitLab remote,
images are uploaded via the uploads API ([gitlab.md](gitlab.md)); GitHub
has no image upload API, so screenshot walkthroughs there always go into
a local report ([github.md](github.md)) with a text-only note pointing at
it.

After an abort, the section is replaced by the abort report described
above — never both.
