# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

WGs and groups of friends splitting everyday shared expenses (rent, groceries, recurring costs) in
long-lived "rooms," not one-off trip settlements. A room member can also be a guest who never
registers — they join and act in a room via an invite without creating an account.

## Product Purpose

Track and split shared expenses inside a room, compute who owes whom, and let people settle debts
(optionally via PayPal). Rooms stay open across an ongoing shared-living or shared-spending
arrangement rather than closing after a single trip.

## Positioning

Two things a neighboring splitting app would not truthfully claim the same way:

- **PWA / offline-first, htmx-driven UI** — installable, low JS overhead, server-rendered swaps
  rather than an SPA.
- **Zero-registration guest entry** — someone can join and use a room as a guest without creating
  an account first; registration is not a gate to participating.

## Operating Context

- Django app (apps/: `account`, `room`, `transaction`, `debt`, `currency`, `importer`, `news`,
  `webpush`, `mail`, `core`, `config`).
- A room is the central object: members, transactions (expenses), debts (computed balances,
  settleable), categories, an activity/news feed, CSV export for transactions and debts.
- `importer` app supports importing existing data into a room.
- Charts (D3) for spend breakdown and trends.
- Push notifications (`webpush`) and email (`mail`), including payment reminders.
- Multi-currency (`currency` app).

## Capabilities and Constraints

- Django + htmx + Idiomorph + Tailwind CSS 4; D3 for charts; PWA with install prompt and offline
  page; webpack-bundled JS/CSS.
- `ModelForm.save()` must only validate/persist — no `transaction.atomic()` ownership, no
  `handle_message()`/side effects; those belong in the view's `form_valid()` (hard rule, see
  AGENTS.md / docs/ai/architecture.md).
- Both light and dark theme are first-class (not a filter over one another); theme applied
  pre-paint, `auto` follows OS.
- Guest accounts exist alongside registered accounts as a first-class concept, not a degraded mode.

## Brand Commitments

- Name **yamsa** is fixed ("Yet another money split app").
- Everything else — palette (`brand` blue token etc.), wordmark, visual identity — is open for
  redesign discussion; nothing beyond the name is a binding constraint.

## Evidence on Hand

- `docs/ai/design.md` — a mature, actively-enforced Tailwind design system: token palette with a
  scripted WCAG contrast contract (`scripts/check_palette_contrast.py`), documented component
  patterns (sheet, card, buttons, badges, radio chips, disclosure), theme handling, and
  interaction rules (edit-in-place sheets, sub-cycles, htmx swap conventions).
- No user research, personas, or usage data on hand beyond the above — no metrics-driven claims.

## Product Principles

1. Rooms are long-lived shared-living context, not one-off trip splits — design for repeated,
   ongoing use, not a single settle-and-forget flow.
2. Guest participation without registration is core, not an edge case — flows must work fully for
   someone with no account.
3. Server-rendered + htmx over SPA: interactions should feel instant via small, targeted swaps, not
   a client-side framework.
4. Both themes are equally first-class; no design decision may implicitly favor one.
5. Every color decision is contract-bound (contrast ratios verified by script) — no visual choice
   overrides that.
