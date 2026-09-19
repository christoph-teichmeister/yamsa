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

**What changed, app-wide** (tokens are global, so every screen inherits them even where its
*structure* wasn't touched this pass):
- Palette: warm kraft/cream neutrals, one committed terracotta accent, replacing the old
  blue-on-cool-gray system. `apps/static_src/tailwind.css`, contrast-verified.
- `font-ledger` (Courier Prime, self-hosted) for amounts/dates/balances — `docs/ai/design.md`'s
  "The index-card box" section documents the exact rule for where it applies.

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

- [ ] **Debts** (`debt/list.html`) — done means: the debt rows (already a list of entries per
      person/direction) move to the same hairline-divided box as the dashboard/feed; balance
      figures take `font-ledger`.
- [ ] **People** (`account/list.html`) — done means: member cards decide whether they're a "list
      of entries" (box treatment) or stay individual (they carry more per-person actions than a
      transaction row does — worth a direction check before assuming the pattern transfers as-is).
- [ ] **Activity** (`news/list.html`) — done means: the timeline's card-per-event treatment is
      reconsidered against the box pattern, or kept if the direction contract judges a timeline a
      genuinely different shape than a ledger list.
- [ ] **Categories** (`transaction/category_manager.html`) — done means: the category list moves
      to the box pattern; category color swatches and the create form get a look pass consistent
      with the new palette (they already inherit the tokens, not yet the structure).
- [ ] **Room sheet** (`room/partials/_room_sheet.html`) — done means: a decision on whether the
      Sheet component itself (docs/ai/design.md "Sheets, not tiles") gets the flatter box
      treatment too, or stays `rounded-3xl` as the correct shape for one-object-detail pages
      (the box pattern was scoped to *lists* — this needs an explicit call, not an assumption).
- [ ] **Auth pages** (login/register/forgot-password, `account/_auth_base.html`) — done means:
      the auth hero's gradient (`auth-hero-surface`, now terracotta-to-dark-brown) and the form
      half both read as the new world, not just recolored blue-shaped chrome.
- [ ] **Guest entry** (`room/partials/_detail_who_are_you.html`) — done means: the same box/seal
      treatment as the member-facing screens, so a guest's first view matches what they see after
      claiming their invitation.
- [ ] **Bottom-nav safe-area gap** — flagged, not fixed, in the header-clipping pass:
      `room/partials/_dashboard_nav.html`'s fixed bottom nav has no `env(safe-area-inset-bottom)`
      term at all (unlike the top bar, which now does). Same bug class, opposite edge.
- [ ] **Room-seal motif and warm-voice copy** — built earlier in this project's identity pass
      (before the redesign was requested), explicitly not protected from replacement. Decide,
      screen by screen as this list is worked through, whether the seal icons and the warm
      empty-state/guest-entry copy survive inside the recipe-card-box world, get adapted (e.g. the
      seal as a literal "stamp" on an index card), or are dropped in favor of something the new
      direction suggests instead.

## Reference

- Direction contract: `.impeccable/surfaces/core-welcome-html.md`
- Palette contract: `scripts/check_palette_contrast.py`
- Component pattern: `docs/ai/design.md` § "The index-card box (a list of entries)"
