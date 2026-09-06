# Design system (Tailwind)

The UI is being migrated from Bootstrap 5 to Tailwind CSS 4, page by page. This document describes
the target system and the rules that keep both frameworks working side by side until the migration
is done.

Migrated so far:

- `account/detail.html` — profile detail
- `account/edit.html` — profile edit

Everything else is still Bootstrap and follows the Bootstrap notes in
[`architecture.md`](architecture.md) § Design System & UI Concepts.

## Coexistence rules

Tailwind is compiled by `@tailwindcss/postcss` from `apps/static/js/tailwind.css` into the
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
   - `button` keeps the UA background → outline and ghost buttons need `tw:bg-transparent`;
   - `select` and `input` are unstyled without `.form-control` → style them fully, `select` needs
     `tw:appearance-none` and its own chevron;
   - `tw:border` sets width only (border color defaults to `currentColor` without Preflight) →
     always pair it with a `tw:border-*` color.

Dropping Bootstrap is a single step: replace the two imports in `tailwind.css` with
`@import "tailwindcss";`, strip the `tw:` prefixes from the templates, and point the `dark` variant
at its own selector.

## Colors

Semantic colors are CSS custom properties that switch with the theme and are exposed to Tailwind via
`@theme inline`. **Prefer them over `dark:` variants** — `tw:bg-surface` is already correct in both
themes. The values mirror `apps/static/base.css`, so a Tailwind page sits flush inside the
Bootstrap shell.

| Token                                          | Use                                                       |
|------------------------------------------------|-----------------------------------------------------------|
| `surface`, `surface-raised`, `surface-sunken`  | card, elevated card, inset panel / page ground            |
| `surface-hover`                                | hover fill for ghost buttons and rows                     |
| `line`, `line-strong`                          | default border, border of interactive elements            |
| `ink`, `ink-muted`, `ink-subtle`               | primary, secondary, tertiary text                         |
| `brand`, `brand-hover`, `brand-text`           | brand fill, its hover, brand-colored text on a surface    |
| `brand-soft`                                   | tinted brand background (badges, icon tiles, gradients)   |
| `on-brand`                                     | text and icons on a brand fill                            |
| `success-*`, `warning-*`, `danger-*`           | `-text` and `-soft` pairs for status                      |

`brand-50` … `brand-900` is the raw ramp for fills that must not shift with the theme.

The theme itself is driven by Bootstrap's `data-bs-theme` attribute on `<html>` (set by
`apps/static/js/navigation.js`), so `tw:dark:…` keys off `[data-bs-theme="dark"]`.

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

## Component patterns

Canonical class strings. Keep them in sync when a pattern changes.

**Page section**

```
tw:@container tw:mx-auto tw:flex tw:w-full tw:max-w-3xl tw:flex-col tw:gap-4
```

**Card** — hero cards add a `tw:bg-gradient-to-br tw:from-brand-soft tw:to-transparent` band and
`tw:rounded-3xl`.

```
tw:rounded-2xl tw:border tw:border-line tw:bg-surface tw:p-5
```

**Primary button**

```
tw:inline-flex tw:items-center tw:justify-center tw:gap-2 tw:rounded-xl tw:bg-brand tw:px-5
tw:py-2.5 tw:text-sm tw:font-semibold tw:text-on-brand tw:shadow-brand tw:transition
tw:hover:bg-brand-hover tw:focus-visible:outline-2 tw:focus-visible:outline-offset-2
tw:focus-visible:outline-brand tw:active:scale-95
```

**Secondary button** — swap `tw:border-line-strong tw:text-ink tw:hover:bg-surface-hover` for
`tw:border-brand tw:text-brand-text tw:hover:bg-brand-soft` to get the brand-outlined variant.

```
tw:inline-flex tw:items-center tw:justify-center tw:gap-2 tw:rounded-xl tw:border
tw:border-line-strong tw:bg-transparent tw:px-5 tw:py-2.5 tw:text-sm tw:font-semibold tw:text-ink
tw:transition tw:hover:bg-surface-hover tw:focus-visible:outline-2
tw:focus-visible:outline-offset-2 tw:focus-visible:outline-brand tw:active:scale-95
```

**Text input** (label: `tw:mb-1.5 tw:block tw:text-sm tw:font-semibold tw:text-ink`, field error:
`tw:mt-1.5 tw:mb-0 tw:text-sm tw:text-danger-text`)

```
tw:w-full tw:rounded-xl tw:border tw:border-line-strong tw:bg-surface-sunken tw:px-4 tw:py-2.5
tw:text-ink tw:transition tw:placeholder:text-ink-subtle tw:focus:border-brand tw:focus:outline-2
tw:focus:outline-offset-0 tw:focus:outline-brand
```

**Badge**

```
tw:inline-flex tw:items-center tw:gap-1.5 tw:rounded-full tw:bg-brand-soft tw:px-2.5 tw:py-1
tw:text-xs tw:font-semibold tw:text-brand-text
```

**Caption above a value**

```
tw:m-0 tw:text-xs tw:font-semibold tw:tracking-wider tw:text-ink-subtle tw:uppercase
```

**Switch** — `shared_partials/_toggle_switch.html`. The input stays a real, hit-testable checkbox
(`opacity-0`, stretched across the track) instead of `sr-only`, so keyboard, screen readers and
Playwright's `check()` keep working.

## Shared partials

- `shared_partials/_toggle_switch.html` — switch-styled checkbox
- `account/shared_partials/_profile_info_tile.html` — icon + caption + value tile

Icons stay on bootstrap-icons (`<i class="bi bi-…" aria-hidden="true">`); that font is independent of
Bootstrap's CSS and outlives the migration.
