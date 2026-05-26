# yamsa Design System v2 – Complete Reference

**Version:** 2.0  
**Status:** Ready for Implementation  
**Tech Stack:** Django + HTMX + Tailwind CSS  
**Target:** Mobile-first, Dark Mode native

---

## 🎨 Color Palette

### Primary Brand Colors

```
Blue (Primary):
  50:   #E6F1FB
  100:  #CCE3F7
  200:  #99C7EF
  300:  #66ABE7
  400:  #338FDF
  500:  #1A7FD8 (base)
  600:  #1566C2
  700:  #0F4FA0
  800:  #0A367E
  900:  #051D5C
  
  Primary Default: #6EA8FE
  Primary Light:   #8DC7FF
  Primary Dark:    #4A7FCC
```

### Semantic Colors

```
Success:  #10B981 (Green)
Warning:  #FF8C42 (Orange)
Danger:   #EF4444 (Red)
Info:     #6EA8FE (Blue – same as primary)
```

### Neutral Colors (Light Mode)

```
Background:       #F6F8FB (--bg-light)
Surface:          #FFFFFF (--bg-white)
Hover:            #F0F2F7 (--bg-hover)
Disabled:         #D6DCE8 (--bg-muted)

Text Primary:     #1F232A (--text-dark)
Text Secondary:   #7C879B (--text-muted)
Text Tertiary:    #9CA3AF (--text-hint)

Border:           #D6DCE8 (--border-light)
```

### Neutral Colors (Dark Mode)

```
Background:       #2D2A2E (--bg-dark) ← KEPT FROM ORIGINAL
Surface:          #3A3740 (--bg-dark-surface)
Hover:            #4A4650 (--bg-dark-hover)
Disabled:         #5A5660 (--bg-dark-muted)

Text Primary:     #F4F6FB (--text-light)
Text Secondary:   #CBD5E1 (--text-light-muted)
Text Tertiary:    #94A3B8 (--text-hint)

Border:           #4C4A4F (--border-dark)
```

---

## 📐 Typography System

### Font Stack

```css
font-family: -apple-system, BlinkMacSystemFont,

"Segoe UI"
,
"Roboto"
,
"Oxygen"
,
"Ubuntu"
,
"Cantarell"
,
"Fira Sans"
,
"Droid Sans"
,
"Helvetica Neue"
,
sans-serif

;
```

### Type Scale (Tailwind Classes)

```
Display:    text-4xl (36px) | font-medium
Heading 1:  text-3xl (30px) | font-semibold
Heading 2:  text-2xl (24px) | font-semibold
Heading 3:  text-xl  (20px) | font-semibold
Body:       text-base (16px) | font-normal
Body Small: text-sm (14px) | font-normal
Label:      text-xs (12px) | font-semibold
Caption:    text-xs (12px) | font-normal

Line Heights:
  Headings: 1.2
  Body: 1.5-1.6
  Captions: 1.3
```

### Font Weights

```
Regular:    font-normal (400)
Medium:     font-medium (500)
Semibold:   font-semibold (600)
Bold:       font-bold (700) – use sparingly
```

---

## 🧩 Component Design

### Buttons

**Primary Button**

```tailwind
class="px-6 py-3 bg-blue-500 text-white rounded-lg font-semibold 
       text-base shadow-md hover:bg-blue-600 active:scale-95 
       transition-all duration-200"
```

- Min height: 44px (mobile tap target)
- Min width: auto
- Radius: 12px (rounded-lg)
- Shadow: md

**Secondary Button**

```tailwind
class="px-6 py-3 bg-transparent border border-gray-300 text-gray-900 
       rounded-lg font-medium text-base hover:bg-gray-100 
       active:bg-gray-200 transition-all duration-200"
```

**Icon Button**

```tailwind
class="w-10 h-10 flex items-center justify-center rounded-lg 
       bg-gray-100 hover:bg-gray-200 active:bg-gray-300 
       transition-colors duration-200"
```

**FAB (Floating Action Button)**

```tailwind
class="fixed bottom-20 right-4 w-14 h-14 rounded-2xl 
       bg-blue-500 text-white flex items-center justify-center 
       text-2xl shadow-lg hover:shadow-xl active:scale-90 
       transition-all duration-200 z-15"
```

### Cards

**Default Card**

```tailwind
class="bg-white dark:bg-slate-800 border border-gray-200 
       dark:border-slate-700 rounded-xl p-4 
       hover:shadow-sm transition-shadow duration-200"
```

**Elevated Card**

```tailwind
class="bg-white dark:bg-slate-800 border-l-4 border-blue-500 
       rounded-xl p-5 shadow-md dark:shadow-lg"
```

**Gradient Card (Stats)**

```tailwind
class="bg-gradient-to-br from-blue-500 to-blue-600 
       text-white rounded-xl p-6 shadow-lg"
```

### Inputs

**Text Input**

```tailwind
class="w-full px-4 py-3 border border-gray-300 dark:border-slate-600 
       bg-gray-50 dark:bg-slate-900 rounded-lg text-base 
       placeholder-gray-500 focus:outline-none focus:ring-2 
       focus:ring-blue-500 focus:border-transparent 
       transition-all duration-200"
```

### Badges

**Badge Base**

```tailwind
class="inline-block px-3 py-1 rounded-full text-xs font-semibold"
```

**Badge Success**

```tailwind
class="inline-block px-3 py-1 rounded-full text-xs font-semibold 
       bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200"
```

**Badge Warning**

```tailwind
class="inline-block px-3 py-1 rounded-full text-xs font-semibold 
       bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-200"
```

### Modals & Dialogs

**Modal Overlay**

```tailwind
class="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center 
       justify-center z-50 p-4"
```

**Modal Content**

```tailwind
class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl 
       max-w-md w-full p-6 max-h-[90vh] overflow-y-auto"
```

### Navigation

**Bottom Navigation**

```tailwind
class="fixed bottom-0 left-0 right-0 bg-white dark:bg-slate-900 
       border-t border-gray-200 dark:border-slate-800 
       flex justify-around py-2 safe-area-bottom"
```

**Bottom Nav Item**

```tailwind
class="flex flex-col items-center justify-center flex-1 py-2 
       text-gray-600 dark:text-gray-400 active:text-blue-500 
       text-xs font-medium gap-1"
```

### Lists & Transactions

**Transaction Card**

```tailwind
class="bg-white dark:bg-slate-800 border border-gray-200 
       dark:border-slate-700 rounded-lg p-4 mb-3 
       flex gap-3 items-center justify-between
       hover:shadow-md active:shadow-sm transition-all"
```

**Icon Badge (Transaction)**

```tailwind
class="w-12 h-12 rounded-lg flex items-center justify-center 
       text-base font-semibold flex-shrink-0"

# Variants:
# Expense:
class="...bg-orange-100 text-orange-600 dark:bg-orange-900 dark:text-orange-300"

# Income:
class="...bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-300"

# Primary:
class="...bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-300"
```

---

## 🎬 Animations & Interactions

### Fade In

```tailwind
class="animate-fade-in"
```

```css
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(4px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.animate-fade-in {
    animation: fadeIn 300ms ease-out;
}
```

### Button Press

```tailwind
active:scale-95 active:shadow-sm transition-all duration-100
```

### Card Hover

```tailwind
hover:shadow-md hover:-translate-y-0.5 transition-all duration-200
```

### Loading Skeleton

```tailwind
class="animate-pulse bg-gray-200 dark:bg-slate-700 rounded"
```

### Toast Slide In

```css
@keyframes toastSlideUp {
    from {
        transform: translateY(100%);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}

.toast {
    animation: toastSlideUp 300ms cubic-bezier(0.34, 1.56, 0.64, 1);
}
```

---

## 🌙 Dark Mode

### Tailwind Dark Mode Setup

```tailwind.config.js
module.exports = {
  darkMode: 'class',
  theme: {
    colors: {
      blue: {
        50: '#E6F1FB',
        100: '#CCE3F7',
        500: '#6EA8FE',
        600: '#4A7FCC',
      },
      // ... other colors
    },
  }
}
```

### HTML Root

```html

<html class="dark"> <!-- or "light" for forced mode -->
```

### CSS Classes Pattern

```tailwind
bg-white dark:bg-slate-800
text-gray-900 dark:text-white
border-gray-200 dark:border-slate-700
```

---

## 📱 Mobile-First Responsive

### Breakpoints

```
Mobile:   0px    (default)
SM:       640px  (small phones)
MD:       768px  (tablets)
LG:       1024px (desktop)
XL:       1280px (large desktop)
```

### Safe Area (Notch Support)

```tailwind
class="pb-safe" <!-- Custom: uses env(safe-area-inset-bottom) -->
pt-[max(1rem,env(safe-area-inset-top))]
pr-[max(1rem,env(safe-area-inset-right))]
pb-[max(1rem,env(safe-area-inset-bottom))]
pl-[max(1rem,env(safe-area-inset-left))]
```

### Padding & Spacing

```
Micro:  space-1   (4px)
XS:     space-2   (8px)
S:      space-3   (12px)
M:      space-4   (16px)  ← default
L:      space-6   (24px)
XL:     space-8   (32px)
```

---

## 🔤 Common UI Patterns

### Header

```tailwind
class="sticky top-0 z-10 bg-white dark:bg-slate-900 
       border-b border-gray-200 dark:border-slate-800 
       px-4 py-3 flex justify-between items-center"
```

### Section Title

```tailwind
class="text-xs font-semibold uppercase tracking-wider 
       text-gray-600 dark:text-gray-400 
       mt-6 mb-3"
```

### Tabs

```tailwind
class="flex gap-0 border-b border-gray-200 dark:border-slate-800 
       mb-6 -mx-4 px-4"

# Tab Button:
class="py-3 px-0 mr-6 border-b-2 border-transparent 
       text-gray-600 dark:text-gray-400 font-medium text-base 
       hover:text-gray-900 dark:hover:text-gray-200
       transition-colors duration-200
       
       # Active state:
       border-blue-500 text-gray-900 dark:text-white"
```

### Search Bar

```tailwind
class="flex items-center gap-3 bg-gray-50 dark:bg-slate-900 
       border border-gray-200 dark:border-slate-700 
       rounded-lg px-3 h-11"
```

### Filter Buttons

```tailwind
class="flex gap-2 overflow-x-auto pb-2 mb-4"

# Filter Button:
class="px-3 py-2 border border-gray-300 dark:border-slate-600 
       bg-transparent rounded-full text-xs font-medium 
       text-gray-600 dark:text-gray-400
       hover:bg-gray-100 dark:hover:bg-slate-800
       transition-colors duration-200
       
       # Active state:
       bg-blue-500 text-white border-blue-500"
```

### Timeline

```tailwind
# Vertical Line:
class="absolute left-5 top-0 bottom-0 w-0.5 
       bg-gradient-to-b from-blue-500 to-blue-500/30"

# Timeline Dot:
class="absolute left-0 top-0 w-11 h-11 rounded-full 
       bg-orange-500 text-white flex items-center justify-center 
       text-sm font-semibold border-4 border-white dark:border-slate-900 
       shadow-md z-10"

# Timeline Content:
class="ml-16 pb-6"
```

### Empty State

```tailwind
class="text-center py-12"

# Icon:
class="text-5xl mb-4"

# Title:
class="text-lg font-semibold text-gray-900 dark:text-white mb-2"

# Text:
class="text-sm text-gray-600 dark:text-gray-400"
```

---

## 🎯 Layout Patterns

### Container with Padding

```tailwind
class="px-4 md:px-6 lg:px-8 py-4"
```

### Sticky Header + Content

```tailwind
# Header:
class="sticky top-0 z-10 ..."

# Content:
class="pb-20" <!-- Account for fixed bottom nav -->
```

### Grid (2-column on mobile, 3-column on desktop)

```tailwind
class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
```

### Flexbox (Horizontal, space-between)

```tailwind
class="flex items-center justify-between gap-2"
```

---

## ✨ Accessibility

### Focus States

```tailwind
focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
dark:focus:ring-offset-slate-900
```

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
    }
}
```

### Contrast Ratios

```
Blue #6EA8FE on White: 5.2:1 (AA)
Blue #6EA8FE on Dark #2D2A2E: 5.8:1 (AA)
Text on cards: Always ≥4.5:1
```

---

## 🛠️ Implementation Checklist

### Tailwind Configuration

- [ ] Install Tailwind CSS (`npm install -D tailwindcss postcss autoprefixer`)
- [ ] Initialize config (`npx tailwindcss init -p`)
- [ ] Add custom colors to `tailwind.config.js`
- [ ] Add custom animations (fadeIn, pulse, etc.)
- [ ] Add safe-area utilities for mobile
- [ ] Test dark mode (`class="dark"` toggle)

### Base Styles

- [ ] Create `base.css` with Tailwind directives
- [ ] Reset default styles (margins, paddings)
- [ ] Define custom utility classes (if needed)
- [ ] Set up font stack and line heights

### Components

- [ ] Build all button variants
- [ ] Build all card variants
- [ ] Build inputs & form controls
- [ ] Build badges, pills, tags
- [ ] Build navigation (top bar, bottom nav, sidebar)
- [ ] Build modals, dialogs, bottom sheets
- [ ] Build timeline components

### Features

- [ ] Dark mode toggle (JavaScript)
- [ ] Search functionality (HTMX)
- [ ] Filters with state management (HTMX)
- [ ] Sorting (sortable columns on table)
- [ ] Animations (fade-in, transitions)
- [ ] Responsive design (test on mobile)

---

## 📝 Usage for AI Agents

### For Component Generation

Use this format when asking an AI to generate components:

```
Generate a [COMPONENT] with these specs:
- Type: [Primary/Secondary/Icon/FAB]
- State: [Normal/Hover/Active/Disabled]
- Theme: [Light/Dark]
- Text: "[Component text]"
- Use Tailwind CSS classes from the yamsa Design System v2
```

### For Layout Generation

```
Generate a [PAGE] layout with:
- Header: [specs]
- Content: [specs]
- Navigation: [specs]
- Use spacing scale: M (16px default)
- Use color palette: Blue for primary, Green/Orange/Red for semantic
- Follow mobile-first responsive pattern
- Ensure dark mode support
```

### For Consistency

Always reference:

1. Color palette (exact hex values)
2. Typography scale (Tailwind class mapping)
3. Component patterns (from this document)
4. Spacing scale (multiples of 4px)
5. Animations (predefined keyframes)

---

## 📚 Related Documents

- **Navigation Roadmap**: `/docs/YAMSA_NAVIGATION_ROADMAP.md`
- **Redesign Plan**: `/docs/YAMSA_REDESIGN_PLAN.md`
- **Tailwind Config**: `tailwind.config.js`
- **Base Styles**: `apps/static/base.css`

---

**Last Updated:** May 2024  
**Maintained By:** Chris (Christopher Teichmeister)  
**Status:** ✅ Production Ready