# Design system (Tailwind)

The UI is being migrated from Bootstrap 5 to Tailwind CSS 4, page by page. This document describes
the target system and the rules that keep both frameworks working side by side until the migration
is done.

Migrated so far:

- `account/detail.html` — the profile page, which reads and edits in the same place
- `account/security.html` — the security settings behind the profile's security rows
- `account/change_password.html` — the password form behind those settings

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

`brand` is a **fill**. As text it lands at 3.25:1 on a dark surface — the token that reads on a
surface is `brand-text`.

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

## Editing in place

The profile sheet does not have a separate edit page. Every value is already its own form control,
`readonly` (or `disabled`, for controls that have no readonly state) until the sheet switches to
edit mode. So:

- Entering edit mode costs **no request**: `profile-sheet.js` flips `data-profile-mode` on the
  sheet and unlocks the controls. Nothing is fetched, nothing re-renders.
- Nothing moves: the same element that showed the value becomes the input, so the text stays where
  it was. What differs between the modes must not change the layout — that is why the action column
  has a fixed width (`tw:@md:w-64`) and the badges sit in their own row: otherwise the wider edit
  actions would squeeze the name and reflow the header.
- Saving posts the sheet and swaps **only the sheet** back in (`hx-target="this"`,
  `hx-swap="outerHTML"`), so the page shell, side menu and scroll position stay untouched. The view
  answers with the sheet partial for htmx requests and redirects for plain ones.

What must **not** go into the edit cycle is anything that only exists while editing and sits
above the fields: it grows the header and pushes every row down. The profile photo used to do
exactly that (an upload hint plus a delete button) and now runs on its own cycle instead — see
below. When in doubt, measure it: `test_entering_edit_mode_does_not_move_the_rows` compares the
first row's offset before and after the switch, on a phone viewport where the header stacks.

Two variants drive the visible difference, `tw:reading:` and `tw:editing:`, keyed off
`data-profile-mode` on the sheet root. Field appearance uses the native `tw:read-only:` and
`tw:disabled:` variants instead, so a control's look follows its actual state rather than a class:

```
tw:border tw:border-line-strong tw:bg-surface-sunken
tw:read-only:border-transparent tw:read-only:bg-transparent tw:read-only:cursor-default
```

Both custom variants are written without `:where()`, which gives them the extra specificity to beat
the plain utility they override (`tw:hidden tw:editing:flex`) whatever the utility order is.

Server and client must agree on the starting state: the template renders `readonly`/`disabled` and
the `data-profile-mode` attribute from `profile_is_editing`, so there is no unlocked flash before
the bundle runs and the page works when it never runs.

Do not add a loading indicator for a swap this small. The save button is disabled for the duration
(`hx-disabled-elt`) and that is the whole feedback; an `htmx-indicator` also keeps its box at
opacity 0 and would widen the button permanently.

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

A `<dialog>` swapped back in with the `open` attribute is *not* in the top layer, so the backdrop
and Escape are dead. `profile-sheet.js` re-opens it with `showModal()` after the swap; check
`:modal`, not the attribute, to tell the two apart.

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

**Text input in a sheet row** — the read-only pair is what makes reading and editing the same
element. Field error: `tw:mt-1.5 tw:mb-0 tw:text-sm tw:text-danger-text tw:reading:hidden`.

```
tw:w-full tw:rounded-lg tw:border tw:border-line-strong tw:bg-surface-sunken tw:px-3 tw:py-2
tw:font-medium tw:text-ink tw:transition tw:placeholder:text-ink-subtle
tw:read-only:cursor-default tw:read-only:border-transparent tw:read-only:bg-transparent
tw:focus:border-brand tw:focus:outline-2 tw:focus:outline-offset-0 tw:focus:outline-brand
```

A `select` cannot be read-only, so it uses `disabled` with the same look plus
`tw:disabled:opacity-100 tw:disabled:text-ink
tw:disabled:[-webkit-text-fill-color:currentcolor]` — without those, browsers grey out its text.
Its chevron carries `tw:reading:hidden`.

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
- `account/partials/_back_to_profile.html` — the back button of the pages behind the profile,
  hooked with `data-back-to-profile` because the side menu also links to the profile
- `account/partials/_password_field.html` — password input with its reveal toggle
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
