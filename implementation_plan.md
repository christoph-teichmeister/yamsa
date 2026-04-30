# Implementation Plan: Issue #144 - Remove Top-Level Loading Spinner

## Phase 1: Core Components
1. Update `.loading-indicator-overlay` CSS to remove `position: fixed`
2. Create `_skeleton.html` partial (configurable item count)
3. Create `_loading_overlay.html` partial (delayed message)
4. Create `_list_loader.html` component (skeleton + overlay logic)

## Phase 2: JavaScript Logic
1. Add HTMX event listeners to show skeleton immediately
2. Add 800ms timeout to switch to overlay
3. Clear overlay when request completes

## Phase 3: Apply Across App
1. List pages: transaction/list, debt/list, room/list, account/list
2. Replace all `hx-indicator="#body-loading-spinner"` with local loaders

## Phase 4: Tests & Docs
1. Unit tests for timing (skeleton path, overlay path)
2. Integration tests for list loads
3. Update component documentation

## Files to Create/Modify
- apps/static/customClasses.css (modify overlay styling)
- apps/templates/shared_partials/_skeleton.html (NEW)
- apps/templates/shared_partials/_loading_overlay.html (NEW)
- apps/templates/shared_partials/_list_loader.html (NEW)
- apps/templates/shared_partials/loading_spinner.html (deprecate)
- [List template files] (apply _list_loader)
