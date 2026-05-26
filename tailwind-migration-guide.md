[//]: # (TODO CT: Delete this file)

# Bootstrap → Tailwind Migration Guide

Quick reference for converting yamsa from Bootstrap to Tailwind CSS.

---

## 🔄 Common Class Mappings

### Layout & Spacing

| Bootstrap   | Tailwind            | Notes                               |
|-------------|---------------------|-------------------------------------|
| `container` | `mx-auto max-w-7xl` | Set max-width in tailwind.config.js |
| `row`       | `flex flex-wrap`    | Use flexbox instead                 |
| `col`       | `flex-1` / `w-full` | Depends on use case                 |
| `col-6`     | `w-1/2 md:w-full`   | Responsive widths                   |
| `p-3`       | `p-3`               | Padding is same (12px)              |
| `m-2`       | `m-2`               | Margin is same (8px)                |
| `my-3`      | `my-3`              | Vertical margin                     |
| `px-4`      | `px-4`              | Horizontal padding                  |

### Display & Visibility

| Bootstrap                 | Tailwind          |
|---------------------------|-------------------|
| `d-flex`                  | `flex`            |
| `d-block`                 | `block`           |
| `d-grid`                  | `grid`            |
| `d-none`                  | `hidden`          |
| `d-none d-md-block`       | `hidden md:block` |
| `flex-column`             | `flex-col`        |
| `justify-content-between` | `justify-between` |
| `align-items-center`      | `items-center`    |
| `gap-3`                   | `gap-3`           |

### Text & Typography

| Bootstrap          | Tailwind                           |
|--------------------|------------------------------------|
| `h1` / `display-1` | `text-4xl font-medium`             |
| `h2`               | `text-2xl font-semibold`           |
| `h3`               | `text-xl font-semibold`            |
| `.text-muted`      | `text-gray-600 dark:text-gray-400` |
| `.text-secondary`  | `text-gray-500`                    |
| `fw-bold`          | `font-bold`                        |
| `fw-semibold`      | `font-semibold`                    |
| `text-center`      | `text-center`                      |
| `text-truncate`    | `truncate`                         |

### Colors & Backgrounds

| Bootstrap        | Tailwind          |
|------------------|-------------------|
| `bg-primary`     | `bg-blue-500`     |
| `bg-light`       | `bg-gray-50`      |
| `bg-white`       | `bg-white`        |
| `text-primary`   | `text-blue-500`   |
| `text-success`   | `text-green-600`  |
| `text-danger`    | `text-red-600`    |
| `border-primary` | `border-blue-500` |
| `border-light`   | `border-gray-200` |

### Borders & Shadows

| Bootstrap        | Tailwind       |
|------------------|----------------|
| `border`         | `border`       |
| `border-0`       | `border-0`     |
| `rounded`        | `rounded-lg`   |
| `rounded-circle` | `rounded-full` |
| `shadow`         | `shadow-md`    |
| `shadow-sm`      | `shadow-sm`    |
| `shadow-lg`      | `shadow-lg`    |

### Interactive States

| Bootstrap     | Tailwind            |
|---------------|---------------------|
| `:hover`      | `hover:`            |
| `:active`     | `active:`           |
| `:focus`      | `focus:`            |
| `:disabled`   | `disabled:`         |
| `.btn:hover`  | `hover:bg-blue-600` |
| `.btn:active` | `active:scale-95`   |

---

## 🎯 Component Patterns

### Buttons

**Bootstrap:**

```html

<button class="btn btn-primary">Click me</button>
<button class="btn btn-secondary">Secondary</button>
<button class="btn btn-outline-primary">Outline</button>
```

**Tailwind:**

```html

<button class="px-6 py-3 bg-blue-500 text-white rounded-lg font-semibold 
               hover:bg-blue-600 active:scale-95 transition-all">
    Click me
</button>

<button class="px-6 py-3 bg-gray-100 text-gray-900 rounded-lg font-medium 
               hover:bg-gray-200 active:scale-95 transition-all">
    Secondary
</button>

<button class="px-6 py-3 border border-blue-500 text-blue-500 rounded-lg 
               font-medium hover:bg-blue-50 active:scale-95 transition-all">
    Outline
</button>
```

---

### Cards

**Bootstrap:**

```html

<div class="card">
    <div class="card-body">
        <h5 class="card-title">Card Title</h5>
        <p class="card-text">Card content here</p>
    </div>
</div>
```

**Tailwind:**

```html

<div class="bg-white dark:bg-slate-800 border border-gray-200 
            dark:border-slate-700 rounded-xl p-6 
            hover:shadow-md transition-shadow">
    <h5 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
        Card Title
    </h5>
    <p class="text-gray-600 dark:text-gray-400">
        Card content here
    </p>
</div>
```

---

### Forms

**Bootstrap:**

```html

<div class="mb-3">
    <label for="email" class="form-label">Email</label>
    <input type="email" class="form-control" id="email"
           placeholder="Enter email">
</div>
```

**Tailwind:**

```html

<div class="mb-4">
    <label for="email" class="block text-sm font-medium text-gray-900 
                            dark:text-white mb-2">
        Email
    </label>
    <input type="email" id="email"
           class="w-full px-4 py-3 border border-gray-300 
                dark:border-slate-600 bg-gray-50 dark:bg-slate-900 
                rounded-lg text-base placeholder-gray-500 
                focus:outline-none focus:ring-2 focus:ring-blue-500 
                focus:border-transparent transition-all"
           placeholder="Enter email">
</div>
```

---

### Grid Layouts

**Bootstrap:**

```html

<div class="row g-4">
    <div class="col-md-6 col-lg-4">Item 1</div>
    <div class="col-md-6 col-lg-4">Item 2</div>
    <div class="col-md-6 col-lg-4">Item 3</div>
</div>
```

**Tailwind:**

```html

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <div>Item 1</div>
    <div>Item 2</div>
    <div>Item 3</div>
</div>
```

---

### Flexbox Layouts

**Bootstrap:**

```html

<div class="d-flex justify-content-between align-items-center gap-3">
    <div>Left</div>
    <div>Right</div>
</div>
```

**Tailwind:**

```html

<div class="flex justify-between items-center gap-3">
    <div>Left</div>
    <div>Right</div>
</div>
```

---

### Responsive Text/Display

**Bootstrap:**

```html
<h1 class="h4 h2-md h1-lg">Responsive Heading</h1>
<p class="d-none d-md-block">Only show on desktop</p>
```

**Tailwind:**

```html
<h1 class="text-2xl md:text-3xl lg:text-4xl font-semibold">
    Responsive Heading
</h1>
<p class="hidden md:block">Only show on desktop</p>
```

---

## 🌙 Dark Mode Pattern

**Bootstrap approach:**

```html

<div class="bg-white text-dark">Light</div>
<!-- Manual dark mode would require extra classes -->
```

**Tailwind approach:**

```html

<div class="bg-white dark:bg-slate-800 text-gray-900 dark:text-white">
    Light and Dark
</div>
```

---

## 🎨 Color Reference

### Yamsa Primary Colors in Tailwind

**Original Bootstrap variable:** `#6EA8FE`

```tailwind
<!-- Primary button -->
<button class="bg-blue-500 hover:bg-blue-600">...</button>

<!-- Primary text -->
<span class="text-blue-500">...</span>

<!-- Primary border -->
<div class="border-blue-500">...</div>

<!-- Primary background (subtle) -->
<div class="bg-blue-50">...</div>
```

### Semantic Colors

```tailwind
<!-- Success -->
<div class="bg-green-50 text-green-700">Success</div>
<div class="dark:bg-green-900 dark:text-green-300">Success Dark</div>

<!-- Warning -->
<div class="bg-orange-50 text-orange-700">Warning</div>
<div class="dark:bg-orange-900 dark:text-orange-300">Warning Dark</div>

<!-- Danger -->
<div class="bg-red-50 text-red-700">Danger</div>
<div class="dark:bg-red-900 dark:text-red-300">Danger Dark</div>
```

---

## 📋 File-by-File Migration Checklist

### CSS Files to Replace

- [ ] `apps/static/base.css` – Replace with Tailwind + custom utilities
- [ ] `apps/static/components/navbar/navbar.css` – Remove (navbar uses Tailwind)
- [ ] `apps/static/components/room/detail.css` – Remove or convert
- [ ] `apps/static/components/transaction/detail.css` – Remove or convert
- [ ] `apps/static/customClasses.css` – Integrate into tailwind utilities
- [ ] `apps/static/htmxIndicatorRequest.css` – Keep but simplify with Tailwind

### Template Files to Update

**High Priority:**

- [ ] `apps/core/templates/core/base.html` – Remove Bootstrap link, add Tailwind
- [ ] `apps/templates/_side_menu.html` – Convert all classes
- [ ] `apps/templates/shared_partials/*.html` – Update all components

**Medium Priority:**

- [ ] `apps/room/templates/room/*.html` – All room templates
- [ ] `apps/transaction/templates/transaction/*.html` – All transaction templates
- [ ] `apps/account/templates/account/*.html` – All account templates

**Low Priority:**

- [ ] Error pages (404, 403, 500)
- [ ] Email templates (if styled)

---

## 🛠️ Migration Steps

### 1. Setup Phase

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 2. Configure Phase

- Create `tailwind.config.js` with yamsa colors
- Update content paths
- Add custom utilities

### 3. CSS Conversion Phase

- Replace `base.css` with Tailwind directives
- Remove Bootstrap CSS link from base.html
- Keep HTMX indicator CSS (or convert)

### 4. Template Conversion Phase

- Start with layout files (_base.html, _side_menu.html)
- Move to component templates
- Finally update page templates

### 5. Testing Phase

- Test all pages in light mode
- Test all pages in dark mode
- Test mobile responsiveness
- Check HTMX functionality

### 6. Cleanup Phase

- Remove old CSS files
- Remove Bootstrap from package.json
- Verify no Bootstrap classes remain

---

## 🔍 Finding Bootstrap Classes

### Search Command

```bash
# Find all Bootstrap classes in templates
grep -r "class=\".*\(btn\|card\|container\|row\|col\)" apps/templates/

# Find Bootstrap CSS files
find apps/static -name "*bootstrap*"

# Count Bootstrap class usage
grep -ro "class=\"[^\"]*\(btn\|card\|form-\)" apps/templates/ | wc -l
```

---

## ✅ Quality Checklist

Before marking migration complete:

- [ ] All pages render correctly in light mode
- [ ] All pages render correctly in dark mode
- [ ] Mobile layout is responsive (320px to 1440px)
- [ ] All interactive elements work (buttons, forms, modals)
- [ ] HTMX functionality preserved (search, filter, etc.)
- [ ] No console errors or warnings
- [ ] Accessibility (keyboard navigation, focus states)
- [ ] Page speed (no regression)
- [ ] Touch targets are 44×44px minimum
- [ ] Text is readable (no very small fonts)
- [ ] Safe area insets respected on mobile notches

---

## 📚 Resources

- **Tailwind Docs:** https://tailwindcss.com/docs
- **Tailwind UI Examples:** https://tailwindui.com/
- **Tailwind Play:** https://play.tailwindcss.com/
- **yamsa Design System:** `docs/DESIGN_SYSTEM_v2.md`
- **Tailwind Config:** `tailwind.config.js`

---

**Estimated Migration Time:** 3-4 weeks (depending on codebase size)  
**Start Date:** [TBD]  
**Target Completion:** [TBD]