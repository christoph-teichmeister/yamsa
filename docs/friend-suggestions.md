## Suggested Guests Experience

- Room creation now surfaces past collaborators via a responsive card grid (
  `apps/room/templates/room/_suggested_guest_list.html`)
- Friend flags persist through the new `UserFriendship` model (`apps/account/models.py`) and can be toggled with the
  HTMX endpoint `room:htmx-suggested-guest-friend-toggle`
- Adding a suggested guest simply toggles a hidden input (`data-suggested-guest-inputs-target`) so the form (
  `room/create.html`) contains the email without exposing it on screen, then the view replays the existing invite logic
  once the room is created
- The feature is powered by `SuggestedGuestService` in `apps/room/services` and surfaced via the `suggested_guest`
  dataclass
