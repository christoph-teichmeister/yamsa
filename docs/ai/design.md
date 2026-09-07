# Design system (Tailwind)

The UI is Tailwind CSS 4 throughout. This document describes the system and the rules a page
follows. Bootstrap 5 was the framework before it; the migration finished by moving the app shell
across, and nothing renders a Bootstrap class any more.

The pages, for orientation:

- `account/detail.html` — the profile page, which reads and edits in the same place
- `account/security.html` — the security settings behind the profile's security rows
- `account/change_password.html` — the password form behind those settings
- `room/detail.html` — the room, editable in place
- `room/create.html` — the new-room form and its suggested guests
- `room/userconnectiontoroom_create.html` and `account/create_guest.html` — adding a member,
  both through `shared_partials/member_form.html`
- `transaction/list.html` with `transaction/partials/_transaction_batch.html` — the expense feed
- `transaction/create.html` and `transaction/edit.html`, with
  `transaction/partials/_category_field.html` and `transaction/child_transaction_create.html`
- `debt/list.html` with `debt/partials/_debt_row_actions.html` — the debt list, its two readings
  and the per-row settle actions
- `debt/settle.html` — the confirmation behind "Mark as paid"
- `importer/upload.html` and `importer/preview.html` — the two steps of an import
- `403.html`, `404.html`, `500.html` and `core/_maintenance_or_offline.html` — the error and
  stand-in pages, all four through `shared_partials/_error_page.html`
- `news/list.html` with `shared_partials/news_card.html`, `shared_partials/_news_card_content.html`
  and `shared_partials/news_batch.html` — the activity timeline
- `core/_welcome.html` with the `room/partials/_room_overview_*` partials,
  `room/partials/_room_balance_summary.html` and `room/partials/_room_create_row.html` — the room
  overview
- `room/partials/_detail_who_are_you.html` — what a room shows someone who is not a member of it
- `account/login.html`, `account/register.html` and `account/forgot_password.html` — the three auth
  pages, all through `account/_auth_base.html`
- `account/list.html` with `shared_partials/user_card.html` and the two
  `shared_partials/invitation_email_*.html` — the room's people
- `account/invite_guest.html` and `account/payment_reminder_unsubscribe.html`
- `transaction/detail.html` with `transaction/partials/_receipts_section.html` — one expense, its
  split and its documents
- `transaction/category_breakdown.html` and `debt`'s `_money_spent_on_room.html` /
  `_money_spent_trend.html` — the three chart pages
- `transaction/category_manager.html` with `transaction/partials/_room_category_creation_form.html`
  and `_room_category_list.html` — the room's categories
- the shell around all of them: `core/base.html`, `_side_menu.html` with `_side_menu_room_list.html`
  and `side_menu_components/room_list_title.html`, `room/partials/_dashboard_nav.html`,
  `shared_partials/toast.html` and the three loader partials — see § What the shell is made of

`mail/email_base.html` is the exception to all of it: mail clients get their own inline CSS.

## How the CSS is put together

Tailwind is compiled by `@tailwindcss/postcss` from `apps/static_src/tailwind.css` into the
`tailwind` webpack bundle. `_head_links_and_scripts.html` loads it after the three hand-written
stylesheets, which is what lets a utility override a component class of the same specificity.

The entrypoint imports the three parts of `tailwindcss` by hand rather than as one, for one
reason: **the utilities must stay out of a cascade layer.** A layered rule loses to an unlayered
one whatever its specificity, and `customClasses.css` is unlayered — `@layer utilities` would put
every utility behind every component rule. Preflight, by the same rule, belongs in `layer(base)`
precisely so those component rules win over it.

Preflight is the app's only reset. Two things it does not do, which `base.css` therefore does:

- the body's background and text colour, and the heading colour — `color-scheme` alone only gets
  a browser's idea of a dark ground, close enough to hide that the palette is not being used;
- the font stack. It is written down because the app's proportions were drawn against it.

Three consequences of Preflight worth keeping in mind when writing a template:

- `*` is reset to `border: 0 solid`, so `border` sets a width and nothing else → always pair it
  with a `border-*` colour;
- `button` and `input` take `font: inherit` and `color: inherit`, so they follow the body unless
  told otherwise — a control that should read as `ink` needs no colour utility, one that should
  not, does;
- `h1`–`h6`, `p`, `ul` and `ol` have no size, weight or margin of their own → set `text-*` and a
  margin utility explicitly. Every page here already does.

## Colors

`apps/static_src/tailwind.css` holds the palette of the **whole app** — the `--yamsa-*` tokens
there are the only place a color is written down. Tailwind exposes them via `@theme inline`;
**prefer them over `dark:` variants** —
`bg-surface` is already correct in both themes.

| Token                                          | Use                                                       |
|------------------------------------------------|-----------------------------------------------------------|
| `canvas`                                       | the page ground, painted on `body`                        |
| `surface`, `surface-raised`, `surface-sunken`  | card, elevated card, inset panel                          |
| `surface-hover`                                | hover fill for ghost buttons and rows                     |
| `line`, `line-strong`                          | default border, border of interactive elements            |
| `ink-strong`, `ink`, `ink-muted`, `ink-subtle` | heading, primary, secondary, tertiary text                |
| `brand`, `brand-hover`, `brand-text`           | brand fill, its hover, brand-colored text on a surface    |
| `brand-soft`                                   | tinted brand background (badges, icon tiles, gradients)   |
| `on-brand`                                     | text and icons on a brand fill                            |
| `scrim`, `on-scrim`                            | the loading overlay's dimming layer, and what stands on it |
| `success-*`, `warning-*`, `danger-*`           | `-text` and `-soft` pairs for status                      |

The `--yamsa-*-border` variables in `tailwind.css` are deliberately **not** in `@theme inline`:
they have no utility of their own, so `border-danger-border` does not compile.
The border of a status control takes the text token at an alpha instead —
`border-danger-text/60`, as the room's close button and the split rows' remove button do.

These tokens are the palette in full. There is no second, theme-independent ramp beside them —
one existed, went unused, and would only have drifted from the tokens that do the work. A colour
that must not shift with the theme is a colour that has not been thought through yet.

`brand-strong`, `scrim` and `on-scrim` are the three that genuinely do not switch, and each has to
argue for it. A scrim does not sit on the canvas but on whatever the page happens to show, and its
job is the same on either theme: push that behind a white spinner. Which also fixes what a
theme-following spinner colour cost — `brand-text` on the old `rgba(0, 0, 0, 0.4)` measured
**2.10:1** on the light theme, under even the 3:1 a graphical object owes; white on `scrim` is
5.82:1 there and 18.63:1 on the dark theme.

Three tokens are kept as bare triplets — `--yamsa-ink-rgb`, `--yamsa-brand-rgb` and
`--yamsa-link-rgb` — because the hand-written stylesheets mix them at an alpha: a row's hover
ground, the skeleton shimmer, the room-list divider, the trend chart's line.

### The values are a contract, not a taste

`scripts/check_palette_contrast.py` (a step in the QA workflow) holds the palette to four rules,
and the numbers in `tailwind.css` are what they are because of them:

- every text token reaches **4.5:1** on *every* opaque ground — `surface`, `surface-raised`,
  `surface-sunken`, `surface-hover` and `canvas`. The hover fill and the raised card are the
  strictest of them, and they are where the first version of this palette failed;
- every `-text` token reaches 4.5:1 on its own `-soft` tint, composited over each of those grounds:
  a tint is translucent, so what a badge label really sits on is the tint *plus* whatever carries
  the badge;
- a button label reaches 4.5:1 on the brand fill **and on its hover** — which is why the brand is
  dark enough to carry white rather than a tint that needs dark text, and why the fill darkens on
  hover in both themes instead of lightening on the dark one;
- `line-strong` (the boundary of inputs and outline buttons) and the brand as a focus ring reach
  **3:1**;
- the neutrals of a theme stay within 20° of hue of each other **and of the other theme's**. A warm
  neutral under a cold brand is what made the old dark theme look muddy — the two sat 59° apart.

Run the script after touching a colour. It prints every failing pair with its measured ratio, and
`--verbose` prints all of them.

### Status colours come in `-text`/`-soft` pairs, never as a fixed hue

A status colour is two tokens, not one: `success-text` on `success-soft`, and the same for
`warning` and `danger`. There is no solid status fill, and there is no third value in between,
because one hue cannot be both a label and a ground — a value that reads as text is too dark for
a fill and vice versa. Measured on this palette a mid-hue label fails on three of the four
grounds, and a yellow one comes out at **1.63:1** on the light theme.

So: never a raw hex in a template or a stylesheet, and never a colour that does not switch with
the theme. If a value seems to need one, it is a value that has not been thought through yet —
`brand-strong`, `scrim` and `on-scrim` are the three exceptions and each argues for itself above.

### One blue per theme

`brand` is the **fill** — a button, a switch, a focus ring, a tinted background — and it *follows
the theme*: a deep blue on the light theme, the same light blue as the text on the dark one. So
`on-brand`, the label standing on it, flips with it: white on light, near-black on dark. A single
fill for both themes cannot work — dark enough to carry white is too dark to read as an accent on
a dark ground, and light enough to read there is too light for a white label.

`brand-text` is what everything read rather than filled takes: text, icons, a chart line, a status bar, the active nav item. On the dark theme it
equals the fill, which is the point — a button, a link and an amount are then one colour.

`brand-strong` is the exception, the one brand tone that does not switch. It belongs to surfaces
that look the same on both themes and carry white either way: the auth hero and the label of the
white button standing on it.

An SVG **presentation attribute does not resolve `var()`** — a d3 chart has to set its colours as
inline styles (`.style("stroke", "var(--yamsa-line)")`), not with `.attr()`, or the chart keeps the
colour it was born with.

## Themes

Both themes are first-class; neither is a filter over the other. Three things carry that:

- **The preference is `light`, `dark` or `auto`**, stored under `theme` in `localStorage`; `auto`
  follows `prefers-color-scheme` and stays selected while the system flips the page.
  `apps/static/js/navigation.js` owns it and marks the chosen button with `aria-pressed`.
- **The theme is applied before the first paint** by the inline script in
  `core/base.html`'s `<head>` — a deferred bundle would show every reader on the other theme a full
  page of the wrong one first. That script does the minimum (read the preference, set
  `data-theme`) and nothing else; it deliberately sits before the stylesheets so it never waits
  for them.
- **`color-scheme` is declared per theme**, next to the tokens. Scrollbars, form controls and every
  other native widget follow the theme through that property alone. The browser's own chrome
  follows `<meta name="theme-color">`, which `navigation.js` re-points at `--yamsa-canvas` on every
  switch.

`dark:…` keys off `[data-theme="dark"]`, the attribute all of this sets.

Radius, spacing and type scale are Tailwind's defaults — they already match the intended scale, so
they are deliberately **not** redefined. Only `--shadow-card`, `--shadow-card-hover` and
`--shadow-brand` are added, because Tailwind's default shadows disappear on a dark ground.

## Layout: use container queries

`#base-content` carries the `app-container` utility, which narrows the column to **50 % width
from 768 px up**. A viewport breakpoint therefore says nothing about the space a page actually has — at a
768 px viewport the content column is only ~384 px wide, narrower than on a phone. Page sections
declare `@container` and use container-query variants:

| Variant  | Container width | Typical use                          |
|----------|-----------------|--------------------------------------|
| `@md` | ≥ 448 px        | stacked → row, wider card padding    |
| `@lg` | ≥ 512 px        | one column → two                     |
| `@xl` | ≥ 576 px        | text and an action side by side      |

## Sheets, not tiles

A settings-style page is **one sheet**, not a grid of cards: a header band with the identity, then
sections of full-width label/value rows separated by hairlines. A row spans the sheet, puts its
label in a fixed-width column (`@md:w-44`) and its value next to it, so values line up down the
page. A card grid says "these are separate things"; on a page where everything belongs to one
object it only adds borders to read past.

Rows that lead somewhere are buttons of the same shape with an icon, a title, a sub-line and a
chevron — never a card with a button in it.

## Form pages behind a sheet

A page a sheet row leads to keeps the same shape: the page section, a `Back to profile` button
above the sheet, then the sheet with its header band. It differs from the profile in two places:

- **The primary action sits in a footer row**, not in the header. The profile's header holds
  Edit/Cancel/Save because that is where the mode lives and the fields are sections away; a
  single-purpose form reads top to bottom and its action belongs after the fields.
- **Labels go above their field**, not in a label column. `Confirm your new password` does not fit
  a `@md:w-44` column on the narrow content shell, and a form is filled in sequence rather than
  scanned down a column of values.

Give such a form `method="post"` and an `action` next to its `hx-post`, so it still submits without
the bundle. htmx pushes the URL it was finally answered from, so a view that redirects on success
leaves the browser on the redirect target rather than on the form.

## Editing in place, without an edit mode

The profile and the room are both one sheet that is **editable wherever it is shown**. There is no
Edit button and no mode: every value is its own form control from the first paint, and an action
row after the last editable section is what carries saving.

That row is the whole of the interaction design, and three things about it are load-bearing:

- **It sits after the fields it acts on**, not in the header. A form is filled top to bottom; a
  Save at the top means typing your way down and then scrolling back up. The header carries the
  identity and the badges, nothing else.
- **Its buttons are disabled until something differs** from what the server rendered.
  `apps/static/js/sheet.js` snapshots the sheet's `FormData` on load and after every swap, and
  compares on `input` and `change`. Discard resets the form and lands back on that snapshot.
- **They render enabled.** A disabled submit would leave the sheet unsubmittable whenever the
  bundle never runs, which is the one state the server cannot detect — so the server renders them
  live and the bundle disables them once it holds the snapshot.

A sheet whose object cannot be edited at all renders **no action row** and its fields carry
`disabled`: a closed room is inert except for its status section, and someone else's profile has
no editable field to begin with.

Saving posts the sheet and swaps **only the sheet** back in (`hx-target="this"`,
`hx-swap="outerHTML"`), so the page shell, side menu and scroll position stay untouched. The view
answers with the sheet partial for htmx requests and redirects for plain ones. The edit URLs
(`account:update`, `room:edit`) are POST targets only — a GET on them redirects to the object,
because there is no separate edit page left to land on.

Do not add a loading indicator for a swap this small. The save button is disabled for the duration
(`hx-disabled-elt`) and that is the whole feedback; an `htmx-indicator` also keeps its box at
opacity 0 and would widen the button permanently.

Dialogs inside a sheet share `apps/static/js/dialog.js` (`data-dialog`,
`data-dialog-open="<id>"`, `data-dialog-close`), which also re-opens a dialog that an htmx swap
brought back with the `open` attribute. Neither bundle knows which page it is on — a second copy
of either would drift from the first.

## Sub-cycles: parts that update on their own

Not everything on a page belongs to the page's own save. The profile photo has its own upload and
delete endpoints, its own narrow form (`ProfilePictureForm`), and swaps only itself
(`hx-target="#profile-photo"`). Three things follow, and they generalise to any part that works
this way:

- **It leaves the rest alone.** Because the swap replaces only the photo, whether the surrounding
  sheet is being edited is never in question — no mode has to be carried through the request and
  back.
- **Its own affordance, in both modes.** The avatar is a button whenever it is on screen, opening a
  dialog that shows the photo full size and offers upload and delete next to it. Nothing about it
  appears or disappears with edit mode.
- **It has to look like a control.** A camera badge alone reads as a status dot — the visual
  language of presence and verified marks — so the avatar also darkens under a centred camera icon
  on hover, carries a `title`, and its `aria-label` names the action ("Change photo"), not the
  object. Hover hints belong on `group-hover:` and, if focus should count,
  `group-has-focus-visible:`; plain `group-focus-within:` fires on mouse focus too and leaves
  the hint stuck over the photo after every click.
- **Its form ignores the rest of the post.** htmx sends the enclosing form's fields along, so the
  narrow form must have exactly the field it owns — every other key is then ignored by
  construction rather than by a filter someone has to maintain.
- **State a script toggles belongs in an attribute, not in a class.** The suggested-guest "Add"
  button carries both labels and both icons and flips only `aria-pressed`; the
  `group-aria-pressed:` variants pick the matching half. `suggested-guests.js` therefore
  assembles no markup and touches no framework class, which is also what keeps those labels
  translatable.

A `<dialog>` swapped back in with the `open` attribute is *not* in the top layer, so the backdrop
and Escape are dead. `dialog.js` re-opens it with `showModal()` after the swap; check `:modal`, not
the attribute, to tell the two apart.

The room's status is the second sub-cycle. Closing a room settles debts, fires an event and decides
whether the fields above it can be edited at all, so it is not a field of the sheet: it posts to
`room:status` with `RoomStatusForm`, which owns `status` and `force_close` and nothing else. Two
details generalise from it:

- **Its trigger carries the payload in `hx-vals`, not in hidden inputs.** A nested `<form>` is
  invalid inside the sheet's own form, and htmx sends the enclosing form's fields along anyway —
  which the narrow form ignores by construction, the same way the photo's does.
- **The event and the debt settlement live in the view's `form_valid()`**, never in the form's
  `save()` — see AGENTS.md § Hard rules. The form only says *whether* this post is the closing
  transition (`closes_the_room`); acting on that is the view's job.

## Component patterns

Canonical class strings. Keep them in sync when a pattern changes.

**Page section**

```
@container mx-auto flex w-full max-w-3xl flex-col gap-4
```

**Sheet** — one object, sections inside it separated by `border-t border-line`, rows inside
a section by `divide-y divide-line`. The header band adds
`bg-gradient-to-br from-brand-soft to-transparent`.

```
@container overflow-hidden rounded-3xl border border-line bg-surface
shadow-card
```

**Card** — for genuinely separate things next to each other, not for the fields of one object.

```
rounded-2xl border border-line bg-surface p-5
```

**Sheet row** — label column plus value, stacking below `@md`.

```
flex flex-col gap-1 px-5 py-3 @md:flex-row @md:items-center @md:gap-4
```

with the label `m-0 text-sm text-ink-muted @md:w-44 @md:shrink-0` and the value in a
`min-w-0 flex-1` wrapper.

**Sheet action row** — `shared_partials/_sheet_actions.html`, right after the last editable
section. Discard is the secondary button, Save the primary one, both with
`disabled:cursor-not-allowed disabled:opacity-50`.

**Section caption**

```
m-0 px-5 pt-4 pb-1 text-xs font-semibold tracking-wider text-ink-subtle
uppercase
```

**Primary button** — `border border-transparent` is load-bearing, see the Preflight notes.

```
inline-flex items-center justify-center gap-2 rounded-xl border
border-transparent bg-brand px-5 py-2.5 text-sm font-semibold text-on-brand
shadow-brand transition hover:bg-brand-hover focus-visible:outline-2
focus-visible:outline-offset-2 focus-visible:outline-brand active:scale-95
```

**Secondary button** — swap `border-line-strong text-ink hover:bg-surface-hover` for
`border-brand text-brand-text hover:bg-brand-soft` to get the brand-outlined variant.

```
inline-flex items-center justify-center gap-2 rounded-xl border
border-line-strong bg-transparent px-5 py-2.5 text-sm font-semibold text-ink
transition hover:bg-surface-hover focus-visible:outline-2
focus-visible:outline-offset-2 focus-visible:outline-brand active:scale-95
```

**Text input in a sheet row** — editable at all times. Field error:
`mt-1.5 mb-0 text-sm text-danger-text`.

```
w-full rounded-lg border border-line-strong bg-surface-sunken px-3 py-2
font-medium text-ink transition placeholder:text-ink-subtle
focus:border-brand focus:outline-2 focus:outline-offset-0 focus:outline-brand
```

A `select` in a row is the same box plus `appearance-none`, `pr-9` and its own
`bi-chevron-down` positioned inside. A sheet that cannot be edited at all renders both with
`disabled`.

**Standalone text input** — outside a row, with a label above
(`mb-1.5 block text-sm font-semibold text-ink`).

```
w-full rounded-xl border border-line-strong bg-surface-sunken px-4 py-2.5
text-ink transition placeholder:text-ink-subtle focus:border-brand focus:outline-2
focus:outline-offset-0 focus:outline-brand
```

**Password field** — `account/partials/_password_field.html`. The reveal toggle sits *inside* the
field box (`absolute inset-y-0 right-0 w-12`) and the input reserves `pr-12` for it;
a button next to the field would shrink the field on the narrow content column. The toggle carries
both labels as data attributes so `password-visibility.js` can swap them without hard-coding
translated text.

Every password input in the app is this partial now — login, register and change-password. Its
`field_name` parameter exists for login alone, whose input must keep Django's own `id_password`
while still posting as `password`, because `e2e/pages/login_page.py` fills it by that id.

**Badge**

```
inline-flex items-center gap-1.5 rounded-full bg-brand-soft px-2.5 py-1
text-xs font-semibold text-brand-text
```

**Navigation row** — a row that leads somewhere, instead of a card with a button in it.

```
flex w-full items-center gap-3 bg-transparent px-5 py-3 text-left
transition hover:bg-surface-hover focus-visible:outline-2
focus-visible:-outline-offset-2 focus-visible:outline-brand
```

with an icon tile (`flex size-9 shrink-0 items-center justify-center
rounded-xl bg-brand-soft text-brand-text`), a `min-w-0 flex-1` text column and a
trailing `bi-chevron-right`.

**Switch** — `shared_partials/_toggle_switch.html`. The input stays a real, hit-testable checkbox
(`opacity-0`, stretched across the track) instead of `sr-only`, so keyboard, screen readers and
Playwright's `check()` keep working.

**Radio chip** — `transaction/partials/_category_field.html`. The label *wraps* its own radio and
reacts to it with `has-checked:`; the radio is stretched across the chip at `opacity-0`, the
same trade as the switch. Two things follow from wrapping rather than pairing: the hit target of a
click on the chip is a descendant of the label, which is what Playwright's `click()` requires, and
no script has to keep a class in sync with `:checked`.

```
relative inline-flex cursor-pointer items-center gap-2 rounded-full border
border-line-strong bg-transparent px-3.5 py-1.5 text-sm font-semibold text-ink
transition hover:bg-surface-hover has-checked:border-brand has-checked:bg-brand-soft
has-checked:text-brand-text has-focus-visible:outline-2
has-focus-visible:outline-offset-2 has-focus-visible:outline-brand
```

**Disclosure section** — a native `<details>`, and no script: the optional fields of the
transaction form open without any bundle having run, and they stay in the DOM either way, so they
post with the form. The summary hides both marker forms (`list-none` plus
`[&::-webkit-details-marker]:hidden`) and the chevron turns with `group-open:rotate-180`.

The room overview's collapsed groups and the guest page's "Not seeing your name?" hint are the same
element. Two things the overview's version shows: the `<summary>` keeps the `.room-overview-toggle`
class and `aria-controls` the e2e suite clicks, and it carries **no** `aria-expanded` — the details
element owns that state, and a static attribute would only ever be a stale copy of it.

## A feed inside a sheet

The transaction list is one sheet whose middle section is an htmx target: `#transaction-feed`
loads `transaction/partials/_transaction_batch.html` on `load` and swaps the next batch in when
the trailing `#transaction-batch-trigger` is `revealed`. Four things about it generalise:

- **A row is a `<button>`**, of the same navigation-row shape as the rows that lead somewhere out
  of a sheet — icon tile, text column, trailing chevron — so Enter and Space need no
  `data-keyboard-click` shim, and it cannot contain a second button. Which is why the eye button
  the old table carried is gone: the row *is* the affordance.
- **The batch renders plain elements, not table rows.** A `<table>` whose single cell held a grid
  needed a stylesheet of `!important` paddings to look like a list; `divide-y divide-line`
  on the feed container is the whole of it now.
- **The search indicator is switched by `display`.** The shared `.htmx-indicator` rule only sets
  `opacity`, which would keep three skeleton rows' worth of empty box above the feed forever, so
  the indicator is `hidden` and reveals itself with `[&.htmx-request]:flex` — htmx sets that
  class on whatever `hx-indicator` names.
- **The anchor highlight is an attribute.** Landing on `…/transactions#transaction-<id>` scrolls
  the row into view and marks it with `data-highlight` for 2.4 s; `data-highlight:bg-brand-soft`
  plus a slow `transition` fades the tint in and out. No keyframes, and the script stays free of
  framework classes.

The "add" affordance is a **floating pill**, fixed above the dashboard's bottom nav
(`bottom-[calc(6rem+env(safe-area-inset-bottom,0px))] z-[1050]`) and below the offcanvas menu
(1200) and the toasts (1400); the page section reserves `pb-16` so the sheet does not end
underneath it.

A dismissible notice carries `data-dismissable` and its close button `data-dismiss`;
`navigation.js` removes the enclosing element, the same way it removes a `.split-row`.

## Shared partials

- `shared_partials/_toggle_switch.html` — switch-styled checkbox; read-only unless
  `toggle_editable` is passed
- `shared_partials/_sheet_value_row.html` — static label/value row, for a value the viewer cannot
  edit in place
- `account/partials/_back_to_profile.html` — the back button of the pages behind the profile,
  hooked with `data-back-to-profile` because the side menu also links to the profile
- `account/partials/_password_field.html` — password input with its reveal toggle
- `shared_partials/_sheet_actions.html` — the save row of a sheet, disabled until something changed
- `shared_partials/member_form.html` — the one-field "add a member" form, shared by the guest and
  the existing-user page; every label reaches it as an already translated parameter
- `room/_suggested_guest_list.html` and `room/_suggested_guest_card.html` — the pick-a-roommate
  cards, on both the create and the add-member page
- `room/partials/_room_sheet.html` — the room, read and edit in one markup
- `room/partials/_room_status_section.html` — closing and reopening, with its confirmation dialog
- `room/partials/_room_status_badge.html` — the open/closed pill
- `account/partials/_profile_sheet.html` — the own profile, read and edit in one markup
- `account/partials/_profile_photo.html` — the avatar, its dialog and its own upload cycle
- `account/partials/_profile_value_row.html` — static label/value row
- `account/partials/_profile_badges.html` — role and PayPal pills
- `transaction/partials/_category_field.html` — the category chips, shared by the create and the
  edit form
- `transaction/partials/_transaction_batch.html` — one batch of the expense feed and its
  reveal-triggered link to the next
- `debt/partials/_debt_row_actions.html` — what one debt row offers: settled badge, PayPal link,
  settle button, or its bare status
- `shared_partials/_error_page.html` — the centred card of the error and stand-in pages;
  `error_action_template` is the optional slot under it, which only the offline page fills
- `shared_partials/_news_card_content.html` — the inside of a news card, shared by its linked and
  its dead variant, which differ only in the box around it
- `room/partials/_room_overview_section.html` — one group of the overview, collapsible or not
- `room/partials/_room_overview_card.html` with `_room_overview_circle.html`,
  `_room_overview_amounts.html` and `_room_overview_status_badge.html` — one room, as a row or as
  a tile
- `room/partials/_room_balance_summary.html` — the open-balance tiles above the overview
- `room/partials/_room_create_row.html` — the overview's "new room" affordance
- `account/_auth_base.html` — the auth pages' shell. Template inheritance rather than an include,
  because both halves are content and an include cannot take two slots
- `account/partials/_auth_hero_cta.html` — the hero's one link out, filled or outlined
- `account/partials/_people_action.html` — one of the two ways to add somebody to a room. It takes
  the *view name*, not the URL: `{% room_url %}` rewrites its own token to append the room slug and
  so cannot be assigned with `as`
- `transaction/partials/_spend_bar.html` — one proportional bar of the spending overview, in three
  tones. Its fill is an inner element with an inline width rather than a `::after` and a custom
  property: a percentage is data, and this way the track and the fill are both plain utilities
- `transaction/child_transaction_create.html` — one more share on the edit form; it must mirror
  that template's split rows down to the `.split-row` hook

`_list_loader.html`, `_loading_overlay.html` and `_user_avatar.html` take their layout and their
colours from `customClasses.css` and the tokens. The pulsing dot both loaders are built from is the
`animate-spinner-grow` keyframe in `tailwind.css`: Tailwind's own `animate-ping` ends at twice the
size, so a row of them would overlap.

State a script toggles must be expressed the way that script expects. `#passkey-reg-result` is
hidden with the `hidden` attribute rather than `hidden`, because `passkey-register.js` reveals
it by clearing that attribute — a utility class would leave the error invisible whatever the script
does. The category suggestion hint and the transaction form's split-lock hint follow the same rule,
and the lock itself sets only real state — `readOnly`, `aria-disabled`, `disabled` — which
`read-only:`, `aria-disabled:` and `disabled:` then render.

Icons are bootstrap-icons (`<i class="bi bi-…" aria-hidden="true">`). It is a standalone icon
font — it never needed the framework it is named after, and it stayed when the framework went.

## Class hooks the tests hold on to

A semantic class survives wherever a test or a script addresses it; the styling moves to utilities
beside it. `.transaction-row` is the first of them, and the room overview is the
largest: `.room-overview-card`, `-name`, `-meta`, `-meta-text`, `-activity`, `-amount(-label|-value)`,
`-toggle`, `-toggle-icon`, `-entries`, `-status`, `.room-overview-card-tile`, `.room-balance-summary`,
`.room-balance-tile.owing|.receiving`, `.room-balance-value` and `.room-status-badge` are what
`e2e/pages/dashboard_page.py` and `apps/core/tests/test_views/test_welcome_partial_view.py` look for.
None of them carries CSS of its own any more.

The transaction pages keep three more: `.transaction-meta` (the first one must name the category —
`e2e/pages/transaction_detail_page.py`), `.transaction-breakdown-item` and `.graph-label`. The
category legend moved the other way: its tests used to select `.list-group-item`, `p.text-muted.small`
and `span.fw-semibold`, and now read `[data-category-legend]`, `[data-category-legend-item]`,
`[data-category-slug-label]` and `[data-category-amount]` — a hook that says what it is beats a
class that says how it looks.

`.room-status-badge` is the one that still has a rule in `customClasses.css`, because the side
menu's room rows use it too. That rule hides the badge below an 18 rem container — written for the
menu panel, but the overview card declares a container as well, so the badge disappeared on exactly
the tiles it is load-bearing for. The overview's badge sets its own `inline-flex`, which wins on
order, and it is visible at every card width now.

## What the shell is made of

The chrome around a page is four things, and none of them needs a component framework:

- **The side menu is a modal `<dialog>`** (`_side_menu.html`, `#side-menu-panel`), opened and
  closed by the `data-dialog-open` / `data-dialog-close` attributes `dialog.js` already carried for
  the photo and room dialogs. That is where its focus trap, its Escape key and its backdrop come
  from. The slide-in is the `side-panel` utility in `tailwind.css`: `@starting-style` and
  `transition-behavior: allow-discrete` are not expressible as utilities, and without the
  `overlay` transition the panel leaves the top layer on the first frame of the close and
  disappears instead of sliding out.
  Being in the top layer it outranks every z-index in the app, the toasts included — a toast
  raised while the menu is open waits behind the scrim.
  A row that navigates carries `data-dialog-close` **and** `hx-trigger="click delay:300ms"`, so
  the panel is shut before htmx swaps the page underneath it.
- **The z-index ladder** is written down where it is used, not in a stylesheet: the ko-fi bar at
  `0`, the dashboard nav at `1030`, the transaction feed's floating pill at `1050`, the top bar at
  `1300`, the toasts at `1400`, the debug banner at `4000` (in `customClasses.css`). The pill is
  positioned against the nav, so the two numbers have to be read together.
- **The content column** is the `app-container` utility — full width on a phone, half the viewport
  from 768 px up — shared by `#base-content`, the top bar and both bottom navs so the chrome stays
  aligned with what it frames.
- **The toast** owns its show/hide/queue in `toast.html`; the tone classes (`toast-primary`,
  `-success`, `-warning`, `-danger`) come from `apps/core/toast_constants.py` and are the four
  `.toast-yamsa-inner` rules in `base.css`. The script reads its base class string off the markup
  rather than keeping a second copy — the two had drifted, and the corner radius changed on the
  first toast of a page.

`room/partials/_room_create_row.html` is the one "new room" affordance, used by the overview and by
the side menu's room list; the menu passes `dismiss_side_menu` to get the two attributes above. It
used to have a second copy in the menu's own design language, which is what having two design
systems cost.

Three page stylesheets went away with these pages and have no replacement:
`components/shared/page-shell.css`, `components/room/overview.css` and `components/news/list.css`.
The auth helpers (`.auth-card`, `.auth-hero`, `.auth-form`, `.hero-cta`, `.auth-page-shell`) and
`.htmx-a` went out of `base.css` and `customClasses.css` with the auth pages, and
`account/list.html` lost the inline `<style>` block that held every `.people-*` rule.

## The auth hero is the one surface that does not follow the theme

`brand-strong` is now in `@theme inline` as `*-brand-strong`, and the hero's two-stop gradient is
an `@utility auth-hero-surface` in `tailwind.css` — a utility rather than a second token because its
far end is a value of that gradient and of nothing else, and this file stays the only place a colour
is written down. Everything standing on the hero takes `text-white` (or `text-white/70`)
outright: the ground is the same on both themes, so a theme-following token would be wrong there.

## What a chart page keeps in CSS

Three pages draw with d3, and utilities cannot reach an element a script creates. So the rule is:
the box around a chart is utilities, what d3 generates is a stylesheet.

- `components/transaction/money-spent-trend.css` is down to `.trend-series` and the three
  `.trend-line-*` rules. Its card, its range switch and its empty state are utilities in
  `_money_spent_trend.html` now.
- `category_breakdown.html` keeps a short inline `<style>`: the legend swatch's colour is *data*
  (`navigation.js` writes `--category-color` from `data-category-color`), and the pie's focus ring
  sits on a `<path>` d3 appends.

Both had a literal `#fff` where they meant the card they sit on — the slice separators and the line
chart's dots. Those are `var(--yamsa-surface)` now, so they read as holes in the shape on either
theme rather than white lines on a dark card. And a d3 colour has to be set with `.style()`, never
`.attr()` — see § Colors.
