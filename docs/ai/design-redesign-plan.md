# Redesign roadmap: the recipe-card-box direction

## What shipped

A real visual redesign, not a refinement: three independent critique cycles (DESIGN_FINDINGS.md)
found yamsa's Tailwind system strong but "structurally generic" — nothing forced "shared
household, long-lived, guest-friendly" identity. The user overrode that conclusion and asked for
an actual redesign via the Impeccable skill's `new-work` flow.

**Direction** (Impeccable `concept-seed --scope direction --mode operate`, seed key `2cd52ce1`,
assigned index 5 of 7 grounded candidates ranked by resonance for a shared-household ledger:
kitchen chalkboard, cork noticeboard, **recipe-card box**, postal lockers, laundry pegboard,
utility meter panel, building directory): every room's ledger is a wooden recipe-card box, every
transaction a typed index card, every room a tabbed divider. No catalog challenger beat it on both
audience identification and product clarity; two raises taken — density from a "Japanese
high-density web" challenger (kills the whitespace-card complaint directly), calm trend-aware
numerals from an "aircraft instrument six-pack" challenger.

**What changed, app-wide** (tokens are global, so every screen inherits them even where its *structure* wasn't touched
this pass):

- Palette: tried warm kraft/cream neutrals with a committed terracotta accent; the user found the
  terracotta accent read as alarm/negative, not warm, and it was reverted to the original
  blue-on-cool-gray values the same session. `apps/static_src/tailwind.css`, contrast-verified
  both ways.
- `font-ledger` (Courier Prime, self-hosted) for amounts/dates/balances — `docs/ai/design.md`'s
  "The index-card box" section documents the exact rule for where it applies. Kept: the color
  complaint was about the accent hue, not the typed-digit amounts.

**What changed, structurally, on the two pilot screens only:**

- Dashboard (`core/_welcome.html` + `room/partials/_room_overview_*.html`): room list rows
  live in one hairline-divided box instead of individually-carded/shadowed tiles; section
  captions read as register tabs.
- Expense feed (`transaction/list.html` + `transaction/partials/_transaction_batch.html`): the
  outer sheet dropped its `rounded-3xl`/`shadow-card` chrome for the same flat box; amounts carry
  `font-ledger`.

Also fixed in the same pass (infra, not identity): the header-clipping bug (`#base-content` now
reserves the top bar's real height including `env(safe-area-inset-top)`), and richer seeded test
data (`create_intensive_test_data`, documented in `docs/ai/testing.md`) so this and future design
passes have real content density to render against.

## What's still on the old sheet/card chrome

Every screen below already reads the new **palette** (tokens are global) but still uses the old
`rounded-3xl ... shadow-card` sheet or `rounded-2xl border ... p-5` card treatment structurally.
Extending the direction to each is a separate, scoped pass — not a blind whole-app pattern-replace,
since each surface's content shape differs (a settings sheet's label/value rows aren't a list of
entries, and the index-card-box pattern is specifically for *lists*, not single-object detail).

- [x] **Debts** (`debt/list.html`) — rows already sat hairline-divided inside the room sheet with
  no per-row card chrome; the only gap was typography, so debt values now carry `font-ledger`,
  same as the dashboard/feed.
- [x] **People** (`account/list.html`) — first pass kept member cards individually boxed
  (`rounded-lg border bg-surface`), lighter than before but still a per-row card; the user called
  this out directly. Reworked into a flat row (`user_card.html`) inside a `divide-y` list, same
  hairline pattern as every other list in the app - the remove action, badges, and
  invitation-status row all fit inline in a row, no box needed.
- [x] **Activity** (`news/list.html`) — header sheet flattened like the rest; each timeline event
  dropped `shadow-card` and the hover lift for a flat border/surface. The rail still separates
  events - that part of a timeline's shape doesn't map onto a hairline list, so events stay
  visually distinct blocks, just without card chrome.
- [x] **Categories** (`transaction/category_manager.html`) — panel and per-category tiles moved
  `rounded-2xl` → the (now-tuned) radius scale, consistent with the rest of the app. Categories
  stayed individual tiles, not a hairline list, the same reasoning as People's per-item actions -
  each one carries its own order input, default toggle, and delete form.
- [x] **Room sheet** (`room/partials/_room_sheet.html`) — the user's call: flatten everywhere, no
  exception for single-object detail. Sheet wrapper moved `rounded-3xl`/`shadow-card` →
  the flat chrome, same as Debts/People/the feed.
- [x] **Auth pages** (login/register/forgot-password, `account/_auth_base.html`) — hero/form shell
  dropped `rounded-3xl`/`shadow-card` for the same flat border chrome as every other screen.
- [x] **Guest entry** (`room/partials/_detail_who_are_you.html`) — sheet and its nested notes
  match the member-facing screens' flat chrome.
- [x] **Bottom-nav safe-area gap** — `_dashboard_nav.html`'s fixed bottom nav now reserves
  `env(safe-area-inset-bottom)`, and `#base-content`'s bottom offset grows with it, mirroring the
  top-bar fix.
- [x] **Global corner radius** — not originally scoped, but the user's actual complaint kept
  coming back to individually-boxed rows and pill-shaped buttons reading as "cards" even after
  the box/shadow removal. Traced to Tailwind's own `rounded-lg`/`xl`/`2xl`/`3xl` defaults
  (8/12/16/24px) being too round for this direction. Fixed once, app-wide, with a
  `--radius-lg`…`--radius-3xl` override in `apps/static_src/tailwind.css` rather than a
  per-template class sweep - landed at a visibly-rounder-than-square middle ground
  (8/10/12/16px) after a too-sharp first pass got rejected too. `rounded-full` (pills, avatars,
  the floating add-transaction button) is untouched by design.
- [ ] **Room-seal motif and warm-voice copy** — built earlier in this project's identity pass (before the redesign was
  requested), explicitly not protected from replacement. Decide,
  screen by screen as this list is worked through, whether the seal icons and the warm
  empty-state/guest-entry copy survive inside the recipe-card-box world, get adapted (e.g. the
  seal as a literal "stamp" on an index card), or are dropped in favor of something the new
  direction suggests instead.

## Reference

- Direction contract: `.impeccable/surfaces/core-welcome-html.md`
- Palette contract: `scripts/check_palette_contrast.py`
- Component pattern: `docs/ai/design.md` § "The index-card box (a list of entries)"
