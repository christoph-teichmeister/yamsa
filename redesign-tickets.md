[//]: # (TODO CT: Delete this file)

# yamsa Redesign – Implementation Tickets

**Project:** yamsa v2 UI Redesign  
**Tech Stack:** Django + HTMX + Tailwind CSS  
**Status:** Ready for Sprint Planning  
**Difficulty:** Medium to High  
**Total Story Points:** ~120

---

## 📋 Phase 1: Foundation (1-2 weeks | 20 SP)

### #1: Setup Tailwind CSS & Design Tokens

**Description:**  
Install and configure Tailwind CSS with yamsa's custom color palette, typography scale, and utility classes.

**Acceptance Criteria:**

- [ ] Tailwind CSS installed and configured
- [ ] Custom colors defined in tailwind.config.js
- [ ] Custom typography scale (Display, H1-H3, Body, Small, Caption)
- [ ] Custom animations (fadeIn, slideUp, pulse)
- [ ] Safe area utilities for mobile notches
- [ ] Dark mode toggle working (`class="dark"`)
- [ ] All custom utilities accessible in templates

**Files to Create:**

- `tailwind.config.js`
- `apps/static/css/base.css` (Tailwind directives)
- `apps/static/css/components.css` (component utilities)

**Estimated:** 4 SP

---

### #2: Create Base Stylesheets & Remove Old CSS

**Description:**  
Remove old Bootstrap CSS, replace with Tailwind base styles. Set up global styles, resets, and utility mixins.

**Acceptance Criteria:**

- [ ] Bootstrap CSS removed
- [ ] Tailwind directives in base.css (@tailwind, @layer, @apply)
- [ ] Default resets applied
- [ ] Font stack configured
- [ ] Light & dark mode colors working globally
- [ ] No CSS class conflicts

**Files to Modify:**

- `apps/static/base.css` (replace with Tailwind)
- `apps/templates/core/base.html` (remove Bootstrap links)
- `package.json` (update build scripts)

**Estimated:** 3 SP

---

### #3: Update HTML Structure for Tailwind

**Description:**  
Audit all templates, replace Bootstrap classes with Tailwind equivalents. Ensure responsive mobile-first approach.

**Acceptance Criteria:**

- [ ] All templates reviewed
- [ ] Bootstrap classes replaced with Tailwind
- [ ] Mobile-first responsive design applied
- [ ] No `style=""` inline styles
- [ ] All components use custom color utilities
- [ ] Dark mode classes applied everywhere

**Files to Modify:**

- `apps/core/templates/core/base.html`
- `apps/templates/_side_menu.html`
- `apps/templates/shared_partials/*.html`
- All app templates

**Estimated:** 6 SP

---

### #4: Design System Documentation Complete

**Description:**  
Finalize design system markdown with all component patterns, color palette, and implementation guidelines.

**Acceptance Criteria:**

- [ ] Design system markdown published
- [ ] All colors documented with hex values
- [ ] All components documented with Tailwind classes
- [ ] Responsive breakpoints explained
- [ ] Dark mode patterns documented
- [ ] AI agent prompt templates included
- [ ] Component checklist complete

**Files to Create:**

- `docs/DESIGN_SYSTEM_v2.md` (in repo)
- `docs/TAILWIND_COMPONENTS.md`

**Estimated:** 4 SP

---

## 📋 Phase 2: Core Components (2 weeks | 25 SP)

### #5: Button Components (All Variants)

**Description:**  
Implement all button variants using Tailwind classes: Primary, Secondary, Icon, FAB, Danger, etc.

**Acceptance Criteria:**

- [ ] Primary button with hover, active, disabled states
- [ ] Secondary button with border & transparent background
- [ ] Icon button (44×44px min)
- [ ] FAB (56×56px, rounded-2xl)
- [ ] Danger button (red styling)
- [ ] All buttons responsive (scaling on mobile)
- [ ] All have proper shadows & transitions
- [ ] Dark mode working

**Template Location:**  
`apps/templates/components/_buttons.html`

**Test Cases:**

- Button states (normal, hover, active, disabled)
- Different sizes (sm, base, lg)
- Light & dark mode rendering

**Estimated:** 3 SP

---

### #6: Card Components (All Variants)

**Description:**  
Implement card layouts: Default, Elevated, Gradient, Transaction cards.

**Acceptance Criteria:**

- [ ] Default card (border, shadow, padding)
- [ ] Elevated card (left border accent, larger shadow)
- [ ] Gradient card (for stats/hero sections)
- [ ] Transaction card (icon + content + amount layout)
- [ ] Proper spacing & typography
- [ ] Hover effects
- [ ] Dark mode colors correct
- [ ] Responsive on mobile

**Template Location:**  
`apps/templates/components/_cards.html`

**Estimated:** 4 SP

---

### #7: Form Inputs & Controls

**Description:**  
Implement text inputs, selects, textareas, checkboxes, radio buttons with focus states.

**Acceptance Criteria:**

- [ ] Text input (44px height, rounded corners)
- [ ] Select dropdown
- [ ] Textarea (with proper resize)
- [ ] Checkbox & radio buttons
- [ ] Focus states with ring (blue)
- [ ] Placeholder styling
- [ ] Error states (red border)
- [ ] Dark mode styling
- [ ] Accessible labels

**Template Location:**  
`apps/templates/components/_forms.html`

**Estimated:** 3 SP

---

### #8: Navigation Components

**Description:**  
Bottom navigation bar, header, tabs, sidebar.

**Acceptance Criteria:**

- [ ] Sticky header (56px mobile, 64px desktop)
- [ ] Bottom navigation (5 tabs, 64px height)
- [ ] Tabs with active indicator
- [ ] Safe area insets applied
- [ ] All navigation responsive
- [ ] Dark mode working
- [ ] Icons visible (Bootstrap Icons)

**Template Location:**  
`apps/templates/components/_navigation.html`

**Estimated:** 4 SP

---

### #9: Badges, Pills & Tags

**Description:**  
Small UI elements for status indicators, labels, counts.

**Acceptance Criteria:**

- [ ] Success badge (green)
- [ ] Warning badge (orange)
- [ ] Danger badge (red)
- [ ] Info badge (blue)
- [ ] Neutral badge (gray)
- [ ] Pill-shaped variants
- [ ] Various sizes (sm, base)
- [ ] Dark mode colors

**Template Location:**  
`apps/templates/components/_badges.html`

**Estimated:** 2 SP

---

### #10: Modals & Bottom Sheets

**Description:**  
Modal dialogs and bottom sheets for mobile actions.

**Acceptance Criteria:**

- [ ] Modal overlay (semi-transparent)
- [ ] Modal content (centered, max-width)
- [ ] Close button
- [ ] Bottom sheet (slides up from bottom)
- [ ] Proper z-index layering
- [ ] HTMX integration for dynamic content
- [ ] Animations (fade + scale for modals, slide for sheets)
- [ ] Dark mode working

**Template Location:**  
`apps/templates/components/_modals.html`

**Estimated:** 3 SP

---

### #11: Toast Notifications

**Description:**  
Toast messages for success, error, info, warning states.

**Acceptance Criteria:**

- [ ] Toast slide-up animation
- [ ] Success toast (green)
- [ ] Error toast (red)
- [ ] Info toast (blue)
- [ ] Warning toast (orange)
- [ ] Auto-dismiss after 4 seconds
- [ ] Dismissable via close button
- [ ] Dark mode background
- [ ] Proper positioning (bottom-left to bottom-center)

**Template Location:**  
`apps/templates/components/_toast.html`

**Estimated:** 2 SP

---

## 📋 Phase 3: Page Templates (3 weeks | 35 SP)

### #12: Home Dashboard Page

**Description:**  
Redesign home/welcome page with balance summary, activity timeline, and quick actions.

**Acceptance Criteria:**

- [ ] Sticky header with yamsa logo
- [ ] Balance cards (Gradient, You owe / You're owed)
- [ ] Activity timeline with vertical line
- [ ] Timeline items with icons & colors
- [ ] Quick action buttons
- [ ] Responsive layout (mobile-first)
- [ ] All animations working
- [ ] Dark mode complete

**Template Location:**  
`apps/core/templates/core/welcome.html`

**Related Tickets:** #14 (Activity Timeline)

**Estimated:** 6 SP

---

### #13: Room Transactions List

**Description:**  
Implement transaction list as searchable, filterable cards (not table).

**Acceptance Criteria:**

- [ ] Search bar (real-time filter)
- [ ] Filter buttons (All, By me, By month)
- [ ] Transaction cards (icon + content + amount)
- [ ] Icons with semantic colors (orange = expense, green = income)
- [ ] Edit/Delete actions (hover to show on desktop, always on mobile)
- [ ] Grouped by month (May 2024, April 2024, etc.)
- [ ] Responsive scrolling
- [ ] Dark mode complete
- [ ] HTMX integration for search/filter

**Template Location:**  
`apps/room/templates/room/partials/_transactions_list.html`

**Related Tickets:** #20 (Room Detail)

**Estimated:** 7 SP

---

### #14: Activity Timeline Component

**Description:**  
Reusable timeline component with vertical line, dots, and events.

**Acceptance Criteria:**

- [ ] Vertical gradient line (blue to transparent)
- [ ] Timeline dots (44px, colored by type)
- [ ] Icons in dots (T, ✓, +)
- [ ] Timeline cards with content
- [ ] Proper spacing & alignment
- [ ] Staggered animations
- [ ] Responsive (full-width on mobile)
- [ ] Dark mode working

**Template Location:**  
`apps/templates/components/_timeline.html`

**Used In:** Home Dashboard, Activity feeds

**Estimated:** 4 SP

---

### #15: Debts Tab (Room Detail)

**Description:**  
Redesign debts view with summary cards and debt list cards.

**Acceptance Criteria:**

- [ ] Summary cards (You owe / You're owed with colors)
- [ ] Debt cards (person avatar + amount + status)
- [ ] Status badges (Unsettled = orange, Settled = green)
- [ ] Primary action buttons (Settle / Remind)
- [ ] Secondary actions (Details / Reopen)
- [ ] Organized in sections (You owe / You're owed)
- [ ] Responsive layout
- [ ] Dark mode complete

**Template Location:**  
`apps/room/templates/room/partials/_debts_list.html`

**Estimated:** 5 SP

---

### #16: Rooms List (Tab View)

**Description:**  
Redesign rooms listing with cards, filters, and create button.

**Acceptance Criteria:**

- [ ] Create Room button (primary, prominent)
- [ ] Filter bar (All, Open, Closed, Recently used)
- [ ] Room cards (icon + name + stats + members)
- [ ] Member avatars preview
- [ ] Status badges (Open = green, Closed = blue)
- [ ] Action buttons (Enter / Edit)
- [ ] Sections (Active rooms / Archived)
- [ ] Responsive grid layout
- [ ] Dark mode complete

**Template Location:**  
`apps/room/templates/room/partials/_rooms_list.html`

**Estimated:** 5 SP

---

### #17: Room Detail Header & Tabs

**Description:**  
Implement room header card with quick stats and navigation tabs.

**Acceptance Criteria:**

- [ ] Gradient header card (blue)
- [ ] Room name, location, member count
- [ ] Quick stats (Total, Your share, Settled %)
- [ ] Tab navigation (Transactions, Debts, Members)
- [ ] Active tab indicator (blue border)
- [ ] Back button
- [ ] Settings menu (⋯)
- [ ] Responsive design
- [ ] Dark mode complete

**Template Location:**  
`apps/room/templates/room/partials/_room_header.html`

**Estimated:** 3 SP

---

### #18: Members Tab (Room Detail)

**Description:**  
Redesign members list with avatars, details, and actions.

**Acceptance Criteria:**

- [ ] Member cards (avatar + name + meta)
- [ ] Join date or transaction count
- [ ] Action buttons (View history / Remove / Edit)
- [ ] Invite member button
- [ ] Responsive layout
- [ ] Dark mode complete

**Template Location:**  
`apps/room/templates/room/partials/_members_list.html`

**Estimated:** 3 SP

---

### #19: Account / Profile Page

**Description:**  
Redesign account settings and profile page.

**Acceptance Criteria:**

- [ ] Profile card (avatar + name + email)
- [ ] Edit profile form
- [ ] Preferences section (theme, language, notifications)
- [ ] Privacy & data section
- [ ] Logout button
- [ ] Responsive layout
- [ ] Dark mode toggle working
- [ ] All form inputs styled

**Template Location:**  
`apps/account/templates/account/detail.html`

**Estimated:** 4 SP

---

### #20: Room Detail View (Complete)

**Description:**  
Integrate all room detail components into final layout.

**Acceptance Criteria:**

- [ ] Header with stats (#17)
- [ ] Transactions tab (#13)
- [ ] Debts tab (#15)
- [ ] Members tab (#18)
- [ ] Tab switching working (HTMX)
- [ ] FAB for add transaction
- [ ] All content responsive
- [ ] Dark mode complete

**Template Location:**  
`apps/room/templates/room/detail.html`

**Depends On:** #13, #15, #17, #18

**Estimated:** 5 SP

---

## 📋 Phase 4: HTMX Integration & Polish (1-2 weeks | 20 SP)

### #21: HTMX Enhancements for Search & Filter

**Description:**  
Add HTMX for real-time search, filtering, and sorting without page reloads.

**Acceptance Criteria:**

- [ ] Search bar triggers server-side filter (hx-get)
- [ ] Filter buttons update transaction list
- [ ] Sort indicators show current sort direction
- [ ] HTMX swaps use `morph:innerHTML` for smooth updates
- [ ] Loading indicators while filtering
- [ ] All HTMX requests debounced (search)
- [ ] Works with browser back button

**Files to Modify:**

- `apps/room/views.py` (add filter/search endpoints)
- `apps/room/templates/room/partials/_transactions_list.html`

**Estimated:** 5 SP

---

### #22: Animations & Transitions

**Description:**  
Add CSS animations for page loads, card interactions, and HTMX swaps.

**Acceptance Criteria:**

- [ ] Fade-in animation on page load
- [ ] Card hover effects (lift + shadow)
- [ ] Button press animation (scale down)
- [ ] Toast slide-up animation
- [ ] Modal fade + scale animation
- [ ] Smooth color transitions on dark mode toggle
- [ ] All animations respect prefers-reduced-motion
- [ ] No janky or flickering animations

**Files to Modify:**

- `apps/static/css/components.css` (animation keyframes)
- `tailwind.config.js` (custom animations)

**Estimated:** 4 SP

---

### #23: Dark Mode Toggle & Persistence

**Description:**  
Implement dark mode toggle button and save preference to localStorage.

**Acceptance Criteria:**

- [ ] Toggle button in sidebar menu
- [ ] Switches between light/dark class on <html>
- [ ] Saves preference to localStorage
- [ ] Reads preference on page load
- [ ] Respects system preference if no saved preference
- [ ] Smooth transition between modes (no flashing)
- [ ] All components render correctly in both modes

**Files to Create/Modify:**

- `apps/static/js/theme-toggle.js` (new)
- `apps/templates/_side_menu.html` (add toggle)

**Estimated:** 3 SP

---

### #24: Mobile Optimization & Safe Areas

**Description:**  
Ensure proper mobile rendering with safe area insets for notches/home indicators.

**Acceptance Criteria:**

- [ ] iPhone notch safe areas respected
- [ ] Home indicator clearance on Android
- [ ] Bottom nav not hidden by home indicator
- [ ] All tap targets ≥44×44px
- [ ] Text readable at 100% zoom
- [ ] No horizontal scroll on mobile
- [ ] Tested on iPhone 12/14, Samsung S21

**Files to Modify:**

- All templates (add pb-safe, pt-safe classes)
- `tailwind.config.js` (safe area utilities)

**Estimated:** 4 SP

---

### #25: Testing & QA

**Description:**  
Cross-browser and cross-device testing, bug fixes.

**Acceptance Criteria:**

- [ ] Tested on Chrome, Safari, Firefox
- [ ] Tested on iPhone 12, iPhone SE, Samsung S21
- [ ] Tablet testing (iPad, Android tablets)
- [ ] Dark mode tested everywhere
- [ ] All buttons clickable on touch
- [ ] Forms work correctly
- [ ] No console errors
- [ ] Lighthouse score ≥85

**Estimated:** 4 SP

---

## 📋 Phase 5: Optional Enhancements (1-2 weeks | 20 SP)

### #26: Transaction Add/Edit Modal (Multi-step)

**Description:**  
Redesign transaction form as multi-step modal for better UX.

**Acceptance Criteria:**

- [ ] Step 1: Basic info (what, amount, date, who paid)
- [ ] Step 2: Split (visual split editor)
- [ ] Step 3: Confirm (review before save)
- [ ] Progress indicator
- [ ] Back/Next navigation
- [ ] HTMX form submission

**Estimated:** 6 SP

---

### #27: Visual Split Editor

**Description:**  
Interactive UI for adjusting transaction splits with drag/tap to modify amounts.

**Acceptance Criteria:**

- [ ] Displays split breakdown visually
- [ ] Allows tapping amounts to adjust
- [ ] Shows total and validates (must sum correctly)
- [ ] Easy add/remove participants
- [ ] Responsive layout

**Estimated:** 5 SP

---

### #28: Room Statistics & Charts

**Description:**  
Add visual charts for spending trends, who spends most, etc.

**Acceptance Criteria:**

- [ ] Bar chart of spending by category
- [ ] Line chart of spending over time
- [ ] Pie chart of who paid what
- [ ] Uses D3.js or Chart.js
- [ ] Dark mode colors working

**Estimated:** 5 SP

---

### #29: Export Functionality UI

**Description:**  
Add UI for exporting room data as CSV/JSON.

**Acceptance Criteria:**

- [ ] Export button in room settings
- [ ] Modal to choose format (CSV/JSON)
- [ ] Download starts automatically
- [ ] Success notification

**Estimated:** 4 SP

---

## 📊 Sprint Breakdown Suggestion

### Sprint 1 (1 week): Foundation

- #1: Tailwind setup
- #2: Base stylesheets
- #4: Design system docs

**Total:** 11 SP

### Sprint 2 (1 week): Core Components

- #5: Buttons
- #6: Cards
- #7: Forms
- #8: Navigation

**Total:** 14 SP

### Sprint 3 (1 week): More Components

- #9: Badges
- #10: Modals
- #11: Toast
- #3: Update templates (parallel with other work)

**Total:** 8 SP + #3 tasks

### Sprint 4 (2 weeks): Pages

- #12: Home dashboard
- #13: Transactions list
- #14: Timeline
- #15: Debts tab

**Total:** 17 SP

### Sprint 5 (2 weeks): More Pages & Integration

- #16: Rooms list
- #17: Room header
- #18: Members tab
- #19: Account page
- #20: Room detail integration
- #21: HTMX enhancements

**Total:** 20 SP

### Sprint 6 (1-2 weeks): Polish

- #22: Animations
- #23: Dark mode toggle
- #24: Mobile optimization
- #25: QA & testing

**Total:** 15 SP

---

## 📝 Notes for Development

### Git Workflow

```bash
# Create feature branch per ticket
git checkout -b feature/#5-button-components

# Commit with ticket reference
git commit -m "#5: Implement primary, secondary, and icon buttons"

# Push and create PR
git push origin feature/#5-button-components
```

### Code Review Checklist

- [ ] Tailwind classes used (no custom CSS unless justified)
- [ ] Dark mode classes applied
- [ ] Responsive design (mobile-first)
- [ ] Accessibility (a11y) checked
- [ ] No Bootstrap classes remaining
- [ ] Component reusable & documented
- [ ] Tested on mobile & desktop

### Testing Commands

```bash
# Tailwind build
npm run tailwind:build

# Watch mode during development
npm run tailwind:watch

# Django development server
python manage.py runserver

# Run tests
python manage.py test
```

---

**Created:** May 2024  
**Last Updated:** May 2024  
**Total Estimated Effort:** ~120 SP (8-10 weeks with 1 full-time dev)