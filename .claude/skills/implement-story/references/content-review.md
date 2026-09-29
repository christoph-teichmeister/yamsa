# Content review: playing the story

The gates prove the code agrees with itself. The review lenses prove it reads correctly. Neither of them
ever loaded a page. This is the phase where the app runs and somebody looks at it.

## What this phase catches, and what it does not

Worth the wall-clock: a flow the player cannot finish, a control wired to nothing, a screen that renders
empty or 500s, a balance number on the page that contradicts the rule the story implemented, a feature no
navigation ever links to.

Not worth it: spacing and colour judgement, anything that needs weeks of real usage to show up, timing
races, and any state you had to hand-edit the database into.

## Getting the app up

```bash
bash .claude/skills/implement-story/scripts/content-server.sh fresh   .claude/runs/<slug>
bash .claude/skills/implement-story/scripts/content-server.sh restart .claude/runs/<slug>
bash .claude/skills/implement-story/scripts/content-server.sh stop    .claude/runs/<slug>
```

`fresh` deletes the smoke sqlite database, migrates, and seeds it via
`manage.py create_intensive_test_data` (users, rooms, categories, transactions, debts). `restart` keeps
the database. **Use `restart` after every code change** - the server runs with `--noreload`, so until you
do, the browser is still testing the code you just replaced.

The script prints the base URL, the login and the log path. It runs on a throwaway SQLite file inside the
run directory (via `DJANGO_DATABASE_URL=sqlite:///<...>/content/smoke.sqlite3`, which this project's
settings accept directly), so nothing here touches the development database.

- Login is by **email address**: `registered_user_1@yamsa.local` / `Admin123$` for an ordinary member, or
  `admin@yamsa.local` for the superuser (same password) - both created by the seed command, hashed
  password is the same for every seeded user. `apps/core/management/commands/create_intensive_test_data.py`
  is the source of truth if a story turns on exact seeded numbers.

## The habits of this app, which decide how you drive it

1. **Most pages are behind login.** A redirect to `/account/login/` means your session is gone, not that
   the feature is broken.
2. **`django-axes` locks an account out after `LOGIN_COUNT` failed attempts.** Do not guess the password -
   the script prints it.
3. **Most of the app needs an active room.** The seed data creates several; without one the nav is nearly
   empty and most URLs have nothing to resolve.
4. **The interactive parts are htmx** (`django-htmx`). `hx-post`/`hx-get` sit on real elements addressable
   by role and name. After a mutating click the URL often does not change; snapshot again to see what
   swapped.
5. **A failing htmx request does not look like a failure** if the frontend swallows the error into a toast.
   **Check network requests after every mutating interaction** - this is the single most missable failure
   class in an htmx app.
6. **Django messages are toasts too**, transient. If you need to read one, snapshot immediately after the
   click.
7. **Static assets are a webpack bundle** (`webpack_bundles/bundles/`, per `webpack.config.js`). The script
   runs `yarn build` if the bundle is missing or stale so JS/Tailwind CSS are current; a `start` that finds
   the run's server already answering reuses it and rebuilds nothing, so after a template/asset change it
   is `restart` that gets you the new bundle, exactly as it is `restart` that gets you the new Python.

## Write the journey before you click

Put it in `content/journey.md` first, as numbered steps with an expected outcome each. A journey written
afterwards is just a description of whatever happened.

The baseline journey runs every time, whatever the story was:

1. Log in as `registered_user_1@yamsa.local`.
2. Land on the dashboard / room list; a seeded room is visible.
3. Open a room; the transaction list and balance/debt summary render.
4. Add a transaction through the form; it appears in the list and the balance updates.
5. Every page the diff touched, whether or not the story mentions it.
6. **`browser_resize` to 390x844, then every page the diff touched again.** Mobile is a first-class
   layout in this project (see `docs/ai/design.md`), and nothing in the test suite asserts on markup, so
   this is the only gate the convention has. What counts is sideways body scroll, a control pushed
   off-screen, or information dropped that desktop gets; spacing judgement is still not a finding. Resize
   back before continuing.

Then the story journey: the steps a player takes to reach and use the new behaviour, straight out of
`spec.md`, with the expected outcome of each written down before you start. Include the failure paths the
story specifies.

## Reaching the state the story needs

Play to it where playing is cheap - the seed data already gives you rooms, categories and a transaction
history. Where playing is not cheap, seed the precondition through the shell:

```bash
DJANGO_DATABASE_URL="sqlite:///$(pwd)/.claude/runs/<slug>/content/smoke.sqlite3" \
  uv run python manage.py shell -c "<python>"
```

**Seed preconditions, never the effect you are checking.** Creating a room the story's feature will act on
is a precondition. Setting the balance the feature is supposed to compute means you tested nothing. If a
state cannot be reached by playing and cannot be seeded without faking the outcome, say so in the journey
and leave the step unverified rather than pretending.

The `admin@yamsa.local` login is a superuser, so `/admin/` is available for reading resulting state when a
page does not show enough of it.

## Observing

- `browser_snapshot` is the default. It is the accessibility tree, it is cheap, and you can quote it.
- `browser_take_screenshot` only when the finding is visual, saved next to the journey in `content/`.
- `browser_network_requests` after every mutating interaction - see habit 5.
- `browser_console_messages` at the end of each leg of the journey.
- `tail` the server log (`content/server.log`) when anything returned 500.

One browser, one tab, driven from this session. Do not hand this phase to parallel agents.

## The browser may be shared with other worktrees on this machine

If the browser tooling in this environment is backed by a single machine-wide daemon rather than one
instance per caller, two content reviews running at once can land in the same browser: one finds the
other's tabs in its snapshot, the other loses its page mid-navigation. If the tool supports an isolated
mode, prefer it. Otherwise:

1. Read the neighbouring worktrees' `state.json`, the same ones Phase 1 scanned. A neighbour whose `phase`
   is `content` and whose `content.status` is still `pending` is the one in the browser. None, no
   contention - go.
2. Message that neighbour, and only it, at the `session` name its `state.json` records. Do not wait in a
   loop and do not follow up.
3. If no answer arrives inside this phase's budget, record `content.status` as `blocked` with the reason
   and ship - a phase that could not run is a gap like any other.

Never close the browser your way out of a collision: on a shared daemon that is the other run's browser
too.

Budget: the baseline journey, the story journey, and **at most ten exploratory interactions beyond them.**

## Recording what you found

Each step in `journey.md` gets a `result:` line - `pass`, or `fail` and the finding it produced. Findings
go in `content/findings.md`:

```content-finding
claim: One sentence stating what a player sees that is wrong.
severity: blocker | high | medium | low
where: URL, and the control you clicked
steps: the shortest path from a fresh smoke database that reproduces it
expected: what the story says should happen
actual: what happened
evidence: the failing request, the console error, the traceback line, or the screenshot path
story-caused: yes | no
```

`story-caused: no` goes to the out-of-scope list, same as in the code review - name it, do not fix it.

## Not a finding

- Styling and spacing, unless the page is unusable.
- Behaviour `spec.md` explicitly put out of scope.
- Anything reproducible only from a database state the app cannot produce.
- Slowness on a first request, which is Django importing itself, not the story.

## When it will not run

- **The server will not start.** The script says why: no virtualenv, no frontend dependencies, migrations
  failed. Fix the environment; if you cannot, the phase is blocked, and that goes in the report.
- **You cannot reach the story's screen at all.** That is not a blocked phase, that is the finding - an
  unreachable feature, severity high.
- **The browser tools are not connected.** Record the phase as skipped with the reason. Never report a
  pass you did not see.
- **A neighbour is already driving the browser.** See above.

## Teardown

Stop the server, pass or fail. A server left running holds the port and serves pre-fix code to the next
run, which is a lie that costs a whole round to notice.
