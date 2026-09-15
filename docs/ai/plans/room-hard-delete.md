# Plan: hard-delete a closed room

Implemented. Decisions taken on the open questions below: deletion is allowed to whoever can
already close the room (no new permission check), remaining members are notified, and the
sheet's "Danger zone" gates the action behind a two-step confirmation dialog, mirroring the
existing force-close dialog.

One thing this plan didn't anticipate: `Room` mixes in `EmitModelCreatedEventOnSaveMixin`,
which auto-fires an event named `<ModelName><Deleted|Created|Changed>` straight after
`Room.delete()`/`.save()`, matched purely by class name. A hand-written `RoomDeleted` event
collided with that convention and fired with the wrong context (`instance` only, after the
cascade had already wiped the data this feature needs). The event is named `RoomHardDeleted`
instead to stay out of that convention's way.

## Goal

Let a user permanently delete a room that is already `CLOSED`. Everything that exists only
because of the room disappears with it. `User` records (guests included) are never deleted —
only the room's own data and its membership rows.

## What actually gets removed

| Model | Relation to Room | Action |
|---|---|---|
| `ParentTransaction` | FK `room`, `on_delete=CASCADE` | cascades, no change needed |
| `ChildTransaction` | FK → `ParentTransaction`, `on_delete=CASCADE` | cascades transitively |
| `Receipt` | FK → `ParentTransaction`, `on_delete=CASCADE` | DB row cascades, but the uploaded **file itself is not removed by CASCADE** — needs an explicit pre-delete step that deletes each `Receipt.file` from storage, or the room's receipts leak in Cloudinary/local storage forever |
| `Debt` | FK `room`, `on_delete=CASCADE` | cascades, no change needed |
| `RoomCategory` | FK `room`, `on_delete=CASCADE` | cascades; only removes the room's *mapping* to a category, the shared `Category` row itself is untouched (correct — categories are global) |
| `UserConnectionToRoom` | FK `room`, `on_delete=CASCADE` | cascades; removes only the membership row, not the `User` |
| `News` | FK `room`, **`on_delete=DO_NOTHING`** | **blocker** — see below |

Explicitly out of scope / must survive:
- `account.User` rows, guest or real — never deleted.
- `currency.Currency` — shared, referenced by `preferred_currency`/`parent_transactions.currency`/`debts.currency` with `PROTECT`/`DO_NOTHING`, never touched.
- `transaction.Category` — shared, `RoomCategory` is the room-specific join row.

## Blocker: `News.room` is `on_delete=models.DO_NOTHING`

`DO_NOTHING` tells Django's collector to leave `News` alone, but the FK constraint still exists at
the DB level. Postgres enforces it as `NO ACTION`, so `room.delete()` will fail with an
`IntegrityError` the moment any `News` row still points at the room — which it always will,
at minimum the `ROOM_CREATED` entry.

Two options:
1. Change `News.room` to `on_delete=models.CASCADE` (needs a migration; matches "news belongs
   only to its room" and is consistent with every other room-owned model above).
2. Keep `DO_NOTHING` and have the delete view/service bulk-delete `room.news.all()` itself before
   deleting the room.

Recommendation: (1) — it's the same rule every other room-owned model already follows, and
removes a footgun for any future FK added the same way. Need to confirm nothing currently reads
`News` after its room is gone (e.g. an admin audit trail) before flipping it; a quick grep shows
no such consumer today.

## Where this hangs together with existing rules

- Deletion is not a `ModelForm.save()` concern (there's nothing to validate/persist), so the
  hard rule in `AGENTS.md` about forms not owning `transaction.atomic()` / side effects doesn't
  directly apply — but the same shape should: the view (or a small service) opens the atomic
  block for the DB deletion, and anything that isn't a DB write (deleting `Receipt` files from
  storage, dispatching a `RoomDeleted`-style event/notification) happens outside/after it, for the
  same reason #333 exists — don't hold a DB connection open across a storage or webpush HTTP call.
- `Room.can_be_closed` is the existing precedent for a similar guard (`not debts.filter(settled=False).exists()`);
  a parallel `Room.can_be_deleted` (or simply "must be `is_closed`") reads the same way.
- The status section (`room/partials/_room_status_section.html`) and the force-close confirmation
  dialog are the existing pattern for a destructive, confirmed room action — a "danger zone"
  section shown only when `current_room.is_closed`, with its own confirmation dialog, fits the
  same sheet (`room/partials/_room_sheet.html`) rather than a new page.

## Open questions (need a product decision before implementing)

1. **Who is allowed to delete?** `RoomMembershipRequiredMixin` currently lets *any* member who
   has seen the room edit or close it — there is no per-room owner/admin role anywhere in the
   app. Hard delete is one-way and destroys other people's transaction history, so it's worth
   deciding explicitly whether to keep that same flat trust model or restrict deletion to
   `room.created_by` (or superusers). Default recommendation: keep it consistent with the rest
   of the app (any member, since that's the existing trust model) unless there's a reason to
   special-case this one action.
2. **Do the other members get told?** Once the room (and its `News`) is gone there's nowhere
   left to show a "this room was deleted" entry. If that matters, the notification (webpush /
   email, reusing `handle_message`) has to be dispatched with the room's name/id captured
   *before* deletion, since the object won't exist afterward.
3. **Confirmation UX** — likely a typed-confirmation or two-step dialog given this is
   irreversible and, unlike closing, cannot be undone by flipping a status back.

## Rough implementation steps (for the follow-up ticket)

1. Migration: `News.room` → `on_delete=models.CASCADE` (pending decision above).
2. `Room.can_be_deleted` property (mirrors `can_be_closed`): `True` only when `is_closed`.
3. Service (`apps/room/services/`) that, inside one transaction: deletes `Receipt` files from
   storage for every receipt in the room, then deletes the `Room` (cascades handle the rest).
4. `RoomDeleteView` (`generic.DeleteView` or a POST-only htmx view, following the
   `RoomStatusUpdateView` shape): membership + `can_be_deleted` check, confirmation dialog,
   redirect to the dashboard on success.
5. "Danger zone" section in `_room_sheet.html`, rendered only for closed rooms.
6. Tests: model test asserting full cascade (transactions/debts/receipts/news/room-categories/
   membership gone, `User` rows untouched); view tests for the `is_closed` guard, the permission
   guard, and the confirmation flow; a storage-cleanup test for receipts.
