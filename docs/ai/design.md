# Design system (Tailwind)

The UI is being migrated from Bootstrap 5 to Tailwind CSS 4, page by page. This document describes
the target system and the rules that keep both frameworks working side by side until the migration
is done.

Migrated so far:

- `account/detail.html` — the profile page, which reads and edits in the same place
- `account/security.html` — the security settings behind the profile's security rows
- `account/change_password.html` — the password form behind those settings
- `room/detail.html` — the room, editable in place
- `room/create.html` — the new-room form and its suggested guests
- `room/userconnectiontoroom_create.html` and `account/create_guest.html` — adding a member,
  both through `shared_partials/member_form.html`

Everything else is still Bootstrap and follows the Bootstrap notes in
[`architecture.md`](architecture.md) § Design System & UI Concepts.

## Coexistence rules

Tailwind is compiled by `@tailwindcss/postcss` from `apps/static_src/tailwind.css` into the
`tailwind` webpack bundle, loaded **after** every Bootstrap stylesheet in
`core/partials/_head_links_and_scripts.html`. Two constraints follow from sharing a page with
Bootstrap, and both are enforced by the CSS entrypoint:

1. **Every utility carries the `tw:` prefix** — `tw:flex`, `tw:bg-surface`,
   `tw:@lg:grid-cols-2`. The prefix comes first, before any variant. Bootstrap and Tailwind share
   class names with different values (`p-3`, `gap-4`, `border`, `rounded`, `shadow-sm`, `container`),
   and since Tailwind loads last, unprefixed utilities would silently re-space every page that is
   still on Bootstrap.
2. **Preflight is off.** Bootstrap Reboot is the base reset. Tailwind's would fight it on the
   Bootstrap pages — but it also means a migrated page gets no reset of its own, so it must be
   explicit about what Reboot already sets:
   - headings keep Reboot's fluid font size and `margin-bottom` → always set `tw:text-*` and a
     margin utility on `h1`–`h6`;
   - `p` keeps `margin-bottom: 1rem` → always set an explicit margin utility;
   - `a` keeps Bootstrap's link color and underline → `tw:no-underline` plus a color utility for
     link-buttons;
   - `button` keeps the UA background **and its UA border** (`2px outset`; Bootstrap resets it
     only in `.btn`) → outline and ghost buttons need `tw:bg-transparent`, and every button
     needs a border of its own: `tw:border tw:border-transparent` on a filled one, so it has
     the same border box as the outlined button beside it and swapping them moves nothing;
   - `select` and `input` are unstyled without `.form-control` → style them fully, `select` needs
     `tw:appearance-none` and its own chevron;
   - `tw:border` sets width only (border color defaults to `currentColor` without Preflight) →
     always pair it with a `tw:border-*` color.

Dropping Bootstrap is a single step: replace the two imports in `tailwind.css` with
`@import "tailwindcss";`, strip the `tw:` prefixes from the templates, and point the `dark` variant
at its own selector.

## Colors

`apps/static_src/tailwind.css` holds the palette of the **whole app** — the `--yamsa-*` tokens
there are the only place a color is written down. Bootstrap has no values of its own:
`apps/static/base.css` maps `--bs-*` onto the same tokens, once, so the two frameworks cannot drift
apart. Tailwind exposes the tokens via `@theme inline`; **prefer them over `dark:` variants** —
`tw:bg-surface` is already correct in both themes.

| Token                                          | Use                                                       |
|------------------------------------------------|-----------------------------------------------------------|
| `canvas`                                       | the page ground the shell paints (Bootstrap's body bg)    |
| `surface`, `surface-raised`, `surface-sunken`  | card, elevated card, inset panel                          |
| `surface-hover`                                | hover fill for ghost buttons and rows                     |
| `line`, `line-strong`                          | default border, border of interactive elements            |
| `ink-strong`, `ink`, `ink-muted`, `ink-subtle` | heading, primary, secondary, tertiary text                |
| `brand`, `brand-hover`, `brand-text`           | brand fill, its hover, brand-colored text on a surface    |
| `brand-soft`                                   | tinted brand background (badges, icon tiles, gradients)   |
| `on-brand`                                     | text and icons on a brand fill                            |
| `success-*`, `warning-*`, `danger-*`           | `-text`, `-soft` and `-border` triples for status         |

These tokens are the palette in full. There is no second, theme-independent ramp beside them —
one existed, went unused, and would only have drifted from the tokens that do the work. A colour
that must not shift with the theme is a colour that has not been thought through yet.

Two tokens are kept as bare triplets, `--yamsa-brand-rgb` and `--yamsa-link-rgb`, because Bootstrap
composes its own colors from `--bs-primary-rgb` and `--bs-link-color-rgb`: a link colour set only as
`--bs-link-color` never reaches an `<a>`.

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

### Bootstrap's own variables are mapped, its utilities are not

`base.css` points Bootstrap's neutrals and status tints at the tokens —
`--bs-body-color-rgb`, `--bs-secondary-color`, `--bs-secondary-bg`, `--bs-tertiary-bg`,
`--bs-emphasis-color`, and the `-text-emphasis` / `-bg-subtle` / `-border-subtle` trio of each
status. So `bg-success-subtle text-success-emphasis` and `bg-body-secondary text-body-emphasis`
**are** the palette, and are the pairs to reach for.

What is *not* mapped is `--bs-primary`/`--bs-success`/`--bs-danger`/`--bs-warning` themselves,
because each drives a text colour (`.text-success`) and a solid fill with forced white text
(`.text-bg-success`) at once: a value that reads as text is too dark for the fill and vice versa.
Which is why the fixed status utilities are out of bounds — measured on this palette,
`.text-danger` and `.text-success` fail on three of the four grounds and `.text-warning` is
**1.63:1** on the light theme, yellow on white.

Never reach for a fixed Bootstrap color — `bg-light`, `text-dark`, `text-bg-light`, `btn-light`,
`btn-close-white`, `text-danger`, `text-success`, `text-warning`, `text-bg-*`, solid `bg-success` —
or a raw hex in CSS. The theme-aware equivalents are the `-subtle`/`-emphasis` pairs,
`bg-body-secondary`, `.btn-surface` (in `base.css`), or a token.

### One blue per theme

`brand` is the **fill** — a button, a switch, a focus ring, a tinted background — and it *follows
the theme*: a deep blue on the light theme, the same light blue as the text on the dark one. So
`on-brand`, the label standing on it, flips with it: white on light, near-black on dark. A single
fill for both themes cannot work — dark enough to carry white is too dark to read as an accent on
a dark ground, and light enough to read there is too light for a white label.

`brand-text` (`text-primary-emphasis` on the Bootstrap side) is what everything read rather than
filled takes: text, icons, a chart line, a status bar, the active nav item. On the dark theme it
equals the fill, which is the point — a button, a link and an amount are then one colour.

`brand-strong` is the exception, the one brand tone that does not switch. It belongs to surfaces
that look the same on both themes and carry white either way: the auth hero and the label of the
white button standing on it.

**Bootstrap's `.btn-outline-*` writes its colours as literals** (`#0d6efd`, `#6c757d`), not from
`--bs-primary`, so `base.css` maps every one of their `--bs-btn-*` variables. Without that an
outline button is a third blue, and the grey one reads at 3.23:1 on a dark surface.

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
  `data-bs-theme`) and nothing else; it deliberately sits before the stylesheets so it never waits
  for them.
- **`color-scheme` is declared per theme**, next to the tokens. Scrollbars, form controls and every
  other native widget follow the theme through that property alone. The browser's own chrome
  follows `<meta name="theme-color">`, which `navigation.js` re-points at `--yamsa-canvas` on every
  switch.

`tw:dark:…` keys off `[data-bs-theme="dark"]`, the attribute all of this sets.

Radius, spacing and type scale are Tailwind's defaults — they already match the intended scale, so
they are deliberately **not** redefined. Only `--shadow-card`, `--shadow-card-hover` and
`--shadow-brand` are added, because Tailwind's default shadows disappear on a dark ground.

## Layout: use container queries

`#base-content` is a Bootstrap `.container-fluid`, which the app narrows to **50 % width from
768 px up**. A viewport breakpoint therefore says nothing about the space a page actually has — at a
768 px viewport the content column is only ~384 px wide, narrower than on a phone. Page sections
declare `tw:@container` and use container-query variants:

| Variant  | Container width | Typical use                          |
|----------|-----------------|--------------------------------------|
| `tw:@md` | ≥ 448 px        | stacked → row, wider card padding    |
| `tw:@lg` | ≥ 512 px        | one column → two                     |
| `tw:@xl` | ≥ 576 px        | text and an action side by side      |

## Sheets, not tiles

A settings-style page is **one sheet**, not a grid of cards: a header band with the identity, then
sections of full-width label/value rows separated by hairlines. A row spans the sheet, puts its
label in a fixed-width column (`tw:@md:w-44`) and its value next to it, so values line up down the
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
  a `tw:@md:w-44` column on the narrow content shell, and a form is filled in sequence rather than
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
  object. Hover hints belong on `tw:group-hover:` and, if focus should count,
  `tw:group-has-focus-visible:`; plain `group-focus-within:` fires on mouse focus too and leaves
  the hint stuck over the photo after every click.
- **Its form ignores the rest of the post.** htmx sends the enclosing form's fields along, so the
  narrow form must have exactly the field it owns — every other key is then ignored by
  construction rather than by a filter someone has to maintain.
- **State a script toggles belongs in an attribute, not in a class.** The suggested-guest "Add"
  button carries both labels and both icons and flips only `aria-pressed`; the
  `tw:group-aria-pressed:` variants pick the matching half. `suggested-guests.js` therefore
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
tw:@container tw:mx-auto tw:flex tw:w-full tw:max-w-3xl tw:flex-col tw:gap-4
```

**Sheet** — one object, sections inside it separated by `tw:border-t tw:border-line`, rows inside
a section by `tw:divide-y tw:divide-line`. The header band adds
`tw:bg-gradient-to-br tw:from-brand-soft tw:to-transparent`.

```
tw:@container tw:overflow-hidden tw:rounded-3xl tw:border tw:border-line tw:bg-surface
tw:shadow-card
```

**Card** — for genuinely separate things next to each other, not for the fields of one object.

```
tw:rounded-2xl tw:border tw:border-line tw:bg-surface tw:p-5
```

**Sheet row** — label column plus value, stacking below `@md`.

```
tw:flex tw:flex-col tw:gap-1 tw:px-5 tw:py-3 tw:@md:flex-row tw:@md:items-center tw:@md:gap-4
```

with the label `tw:m-0 tw:text-sm tw:text-ink-muted tw:@md:w-44 tw:@md:shrink-0` and the value in a
`tw:min-w-0 tw:flex-1` wrapper.

**Sheet action row** — `shared_partials/_sheet_actions.html`, right after the last editable
section. Discard is the secondary button, Save the primary one, both with
`tw:disabled:cursor-not-allowed tw:disabled:opacity-50`.

**Section caption**

```
tw:m-0 tw:px-5 tw:pt-4 tw:pb-1 tw:text-xs tw:font-semibold tw:tracking-wider tw:text-ink-subtle
tw:uppercase
```

**Primary button** — `tw:border tw:border-transparent` is load-bearing, see the Preflight notes.

```
tw:inline-flex tw:items-center tw:justify-center tw:gap-2 tw:rounded-xl tw:border
tw:border-transparent tw:bg-brand tw:px-5 tw:py-2.5 tw:text-sm tw:font-semibold tw:text-on-brand
tw:shadow-brand tw:transition tw:hover:bg-brand-hover tw:focus-visible:outline-2
tw:focus-visible:outline-offset-2 tw:focus-visible:outline-brand tw:active:scale-95
```

**Secondary button** — swap `tw:border-line-strong tw:text-ink tw:hover:bg-surface-hover` for
`tw:border-brand tw:text-brand-text tw:hover:bg-brand-soft` to get the brand-outlined variant.

```
tw:inline-flex tw:items-center tw:justify-center tw:gap-2 tw:rounded-xl tw:border
tw:border-line-strong tw:bg-transparent tw:px-5 tw:py-2.5 tw:text-sm tw:font-semibold tw:text-ink
tw:transition tw:hover:bg-surface-hover tw:focus-visible:outline-2
tw:focus-visible:outline-offset-2 tw:focus-visible:outline-brand tw:active:scale-95
```

**Text input in a sheet row** — editable at all times. Field error:
`tw:mt-1.5 tw:mb-0 tw:text-sm tw:text-danger-text`.

```
tw:w-full tw:rounded-lg tw:border tw:border-line-strong tw:bg-surface-sunken tw:px-3 tw:py-2
tw:font-medium tw:text-ink tw:transition tw:placeholder:text-ink-subtle
tw:focus:border-brand tw:focus:outline-2 tw:focus:outline-offset-0 tw:focus:outline-brand
```

A `select` in a row is the same box plus `tw:appearance-none`, `tw:pr-9` and its own
`bi-chevron-down` positioned inside. A sheet that cannot be edited at all renders both with
`disabled`.

**Standalone text input** — outside a row, with a label above
(`tw:mb-1.5 tw:block tw:text-sm tw:font-semibold tw:text-ink`).

```
tw:w-full tw:rounded-xl tw:border tw:border-line-strong tw:bg-surface-sunken tw:px-4 tw:py-2.5
tw:text-ink tw:transition tw:placeholder:text-ink-subtle tw:focus:border-brand tw:focus:outline-2
tw:focus:outline-offset-0 tw:focus:outline-brand
```

**Password field** — `account/partials/_password_field.html`. The reveal toggle sits *inside* the
field box (`tw:absolute tw:inset-y-0 tw:right-0 tw:w-12`) and the input reserves `tw:pr-12` for it;
a button next to the field would shrink the field on the narrow content column. The toggle carries
both labels as data attributes so `password-visibility.js` can swap them without hard-coding
translated text.

**Badge**

```
tw:inline-flex tw:items-center tw:gap-1.5 tw:rounded-full tw:bg-brand-soft tw:px-2.5 tw:py-1
tw:text-xs tw:font-semibold tw:text-brand-text
```

**Navigation row** — a row that leads somewhere, instead of a card with a button in it.

```
tw:flex tw:w-full tw:items-center tw:gap-3 tw:bg-transparent tw:px-5 tw:py-3 tw:text-left
tw:transition tw:hover:bg-surface-hover tw:focus-visible:outline-2
tw:focus-visible:-outline-offset-2 tw:focus-visible:outline-brand
```

with an icon tile (`tw:flex tw:size-9 tw:shrink-0 tw:items-center tw:justify-center
tw:rounded-xl tw:bg-brand-soft tw:text-brand-text`), a `tw:min-w-0 tw:flex-1` text column and a
trailing `bi-chevron-right`.

**Switch** — `shared_partials/_toggle_switch.html`. The input stays a real, hit-testable checkbox
(`opacity-0`, stretched across the track) instead of `sr-only`, so keyboard, screen readers and
Playwright's `check()` keep working.

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

State a script toggles must be expressed the way that script expects. `#passkey-reg-result` is
hidden with the `hidden` attribute rather than `tw:hidden`, because `passkey-register.js` reveals
it by clearing that attribute — a utility class would leave the error invisible whatever the script
does.

Icons stay on bootstrap-icons (`<i class="bi bi-…" aria-hidden="true">`); that font is independent of
Bootstrap's CSS and outlives the migration.
