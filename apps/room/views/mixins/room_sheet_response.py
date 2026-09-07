from django.http import HttpResponse
from django.template.loader import render_to_string

from apps.room.forms import RoomEditForm

ROOM_SHEET_TEMPLATE = "room/partials/_room_sheet.html"


class RoomSheetResponseMixin:
    """Render just the room sheet, for the htmx swaps that replace it in place."""

    def is_htmx_request(self) -> bool:
        return self.request.headers.get("HX-Request") == "true"

    def render_room_sheet(self, room, *, form=None, status_form=None) -> HttpResponse:
        """Answer with the sheet alone, so the browser keeps the page it is already on.

        `request.room` is loaded by the middleware before the view runs, so a save leaves the
        `current_room` the context processor builds from it one version behind. Re-pointing it at
        the saved room is what keeps the swapped sheet — and the shell around it — in step.
        """

        self.request.room = room

        return HttpResponse(
            render_to_string(
                ROOM_SHEET_TEMPLATE,
                {
                    "room": room,
                    "form": form if form is not None else RoomEditForm(instance=room),
                    "status_form": status_form,
                    "open_debt_count": room.debts.filter(settled=False).count(),
                },
                request=self.request,
            )
        )
