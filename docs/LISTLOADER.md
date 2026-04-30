# ListLoader Component (Issue #144)

## Overview

The **ListLoader** component provides a non-intrusive loading experience for list views:

1. **Skeleton Screen** (0–800ms): Instant placeholder items
2. **Overlay with Message** (>800ms): "Das dauert länger als erwartet!"

## Usage

```django
<div id="transaction-list" hx-get="{% url 'transaction:api_list' %}" hx-swap="innerHTML">
    {% include "shared_partials/_list_loader.html" with 
       loader_id="transaction-list"
       skeleton_count=5 %}
</div>
```

## Features

✅ Non-blocking (page interactive)  
✅ Instant skeleton feedback  
✅ Delayed overlay (>800ms)  
✅ German localization  
✅ HTMX integration  

## Files

- `_skeleton.html` — Skeleton items with shimmer
- `_loading_overlay.html` — Delayed overlay message
- `_list_loader.html` — Main component

## Testing

```bash
pytest apps/room/tests/test_list_loader.py -v
```

See `IMPLEMENTATION_SUMMARY.md` for complete architecture and acceptance criteria.
