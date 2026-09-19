# Design findings tracker

Working tracker for `/impeccable critique` findings across yamsa surfaces, kept so nothing
falls through between sessions. Not a permanent doc — delete once everything below is closed.

Full critique reports: `.impeccable/critique/`.

## Dashboard (`core/_welcome.html`) — critique 2026-09-19, score 29/40

Priority issues:

- [x] P0 — No arrival moment / personalization → greeting + biggest-open-balance highlight added
- [x] P1 — No search/filter, "Other" unbounded → search box (`show_room_search`, >6 rooms)
- [ ] P1 — No error/stale state → **resolved as no-op**: synchronous ORM reads, no cache/API
  layer, a DB failure already goes through the 500 page. Fabricating a degraded state here
  would violate AGENTS.md ("no error handling for scenarios that can't happen").
- [x] P2 — Empty state under-designed → house icon added
- [x] P3 — No help for Open/Closed/Other → legend `<details>` added
- [x] Guest visibility — guest badge added to header (was invisible before)

Minor observations:

- [x] Balance-summary tiles untested with 4+ active currencies → added
  `test_the_summary_holds_several_currencies_without_crowding`, confirmed no crowding/crash
- [x] Closed-room initials circle (`bg-danger-soft`) duplicates the status badge → always
  brand-toned now, status badge alone carries the "Closed" signal
- [ ] Dashboard card shows a bare timestamp with no hint of *what* happened → **left as-is**:
  the news feed was deliberately excluded from this context, and there's no other source of
  "what happened" without reintroducing that dependency. Not actioned.
- [x] No dark-theme visual pass done → **verified structurally**: every template touched this
  session (dashboard, feed, room sheet) uses only semantic token utilities, zero hardcoded
  colors (checked via grep). Still no real-browser pixel check — see Cross-cutting note below.

## Ausgaben-Feed (`transaction/list.html`) — critique 2026-09-19, score 27/40

Priority issues:

- [x] P1 — Touch targets under 44×44pt (add pill, dismiss, "Clear filter") → sized up
- [x] P1 — Category/currency filter UI "dead" → **false finding**, verified live: already linked
  from `category_breakdown.html`'s legend, works end-to-end. No action needed.
- [x] P1 — No inline error state on feed/search failure → added to shared `_list_loader.html`
  (also benefits the news feed, which reuses it)
- [x] P2 — No date-group landmarks in the feed → `naturalday` labels via `{% ifchanged %}`
  (caveat: a date can repeat once across a batch-load boundary — accepted trade-off)
- [x] P3 — Amount doesn't outrank description in hierarchy → bumped to `text-base`

Minor observations:

- [x] Inconsistent vocabulary: "Expenses" eyebrow → "Transactions", matching the h1/CTA/Tips
- [x] CSV export link doesn't say what's exported → title now reads "Exports every transaction in
  the room, not just your current search or filter" (confirmed via code read: the export view
  genuinely ignores all filters/search, so the copy states the real behavior, not a promise)
- [x] Truncated description has no `title` tooltip → added, full untruncated text
- [x] Import-hint dismiss persistence unclear → **false observation**, verified in code:
  `_pop_import_share_hint()` is a session-popped one-shot server-side, not a client-persisted
  dismiss — a reload never shows it twice regardless of the dismiss button. No action needed.
- [x] Skeleton/batch-size mismatch (5 vs 10) → skeleton bumped to 10 to match
  `TRANSACTION_FEED_PAGE_SIZE`

Bug found while testing (pre-existing, confirmed red on `main` too, unrelated to any fix above):

- [x] `test_category_breakdown_legend_links_to_filtered_transaction_list` fails —
  `&currency=` renders as `&curren;cy=` (HTML entity `¤`). **Root cause: not an app bug** — the
  app's own HTML is spec-correct (a browser doesn't resolve a named entity inside an attribute
  value when it's followed by an alphanumeric character, per the HTML5 parsing spec, and
  "currency" is followed by "c"). The test used `BeautifulSoup(..., "html.parser")`, and Python's
  stdlib `html.parser` doesn't implement that spec rule, so it mis-decoded the attribute only in
  the test tool, not in any real browser. Fixed by switching that test file to the spec-compliant
  `html5lib` parser (added as a dev dependency) instead of changing the (already correct) app
  output.

## Cross-cutting / infra

- [ ] **Terser minification is currently disabled** (`optimization.minimize: false` applied ad hoc,
  not committed to `webpack.config.js`) as a workaround for a `htmx.defineExtension is not a
      function` runtime break in the ProvidePlugin↔idiomorph integration under production
  minification. Root cause not fully isolated — needs a proper fix in `webpack.config.js`
  before minification can be safely re-enabled.
- [ ] **No real mobile-browser visual verification** has been done for any change in this
  tracker — everything was checked via curl/rendered-HTML inspection and unit tests only (no
  Chrome extension access in this session). Given yamsa is mobile-first, a real device/viewport
  pass is owed before calling any of the above "done" in spirit, not just in code.

## Room sheet (`room/detail.html`) — critique 2026-09-19, score 25/40

Priority issues:

- [x] P0 — No confirmation on the common "Close room" path → same confirm-dialog pattern as
  force-close/delete now applies to the happy path too (`close-room-dialog`)
- [x] P1 — Disabled fields have no distinct visual state → `disabled:opacity-60
      disabled:cursor-not-allowed` added to name/description/currency
- [x] P2 — Member count is a dead end → turned into a navigation row linking to the People tab
- [x] P3 — "Closing readiness" duplicates the Status section → removed, Status section owns it
  exclusively now

Minor observations:

- [x] Description field had no visible character counter → live `x/50` counter added (`description-counter`, updates on
  input)
- [x] `preferred_currency` comparison was inline template logic → moved to
  `RoomEditForm.selected_currency_id`, template now does one plain comparison
- [x] Bottom-nav active tab distinguished by color alone → active tab now also gets a
  `bg-brand-soft` pill, a shape/fill cue independent of color
- [x] Long room description truncation elsewhere → **false observation**, verified:
  `_room_overview_card.html` already truncates `meta_text` (which carries the description)
  wherever it's shown. No action needed.

Note: could not visually confirm the new `close-room-dialog` renders correctly via curl — the only
seeded room with debts open showed the *other* (force-close) branch. Logic mirrors the
already-tested force-close/delete dialogs exactly, and the room test suite (165 passed) covers the
underlying assertions, but a real click-through on a debt-free room is still owed.

## Surfaces not yet critiqued

None from the original shortlist — dashboard, transaction feed, and room sheet are all done. Next
candidates would need a fresh shortlist if this continues.

---

Chris: okay, aber so wirklich redesigned haben wir hier jetzt nichts, oder? Nur ein paar UX Bugs behoben

Claude: Richtig — bisher zwei Critique→Fix-Zyklen (Dashboard, Ausgaben-Feed), also Politur, kein Redesign. Beide
Critiques kamen unabhängig zum selben Design-Specificity-Verdict: das Tailwind-System selbst (Tokens, Kontrast-Contract,
Komponenten) ist stark und korrekt angewendet, aber die Screens selbst könnten strukturell zu fast jeder generischen
List-/Splitting-App gehören — nichts zwingt visuell "geteilter Haushalt, langlebig, gastfreundlich" auf den ersten
Blick. Meine Einschätzung: das ist kein Trigger für ein komplettes visuelles Redesign (neue Palette/Wortmarke/Look) —
das bestehende System wegzuwerfen wäre Verschwendung von echt gutem, getestetem Fundament. Der eigentliche Hebel wäre
eher Charakter/Identität innerhalb des bestehenden Systems draufsetzen: ein visuelles Signature-Element für "Room" als
Konzept, mutigere Illustration/Icon-Sprache statt generischer Initialen-Kreise, eine eigene Stimme für
Empty-States/Onboarding — das wäre /impeccable bolder oder /impeccable delight auf breiterer Front, nicht new-work
(kompletter Weltwechsel). Willst du das als nächstes angehen — echte Identitäts-Injektion statt weiterer Bugfix-Zyklen?
