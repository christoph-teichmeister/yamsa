from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View

from apps.room.views.mixins.room_sheet_response import RoomSheetResponseMixin


class RoomSealResetView(RoomSheetResponseMixin, View):
    """Clear any chosen icon or uploaded image, back to the room's derived default seal."""

    def post(self, request, *args, **kwargs):
        room = request.room
        if room.seal_image:
            room.seal_image.delete(save=False)
        room.seal_image = None
        room.seal_icon = ""
        room.save(update_fields=["seal_icon", "seal_image"])

        if self.is_htmx_request():
            return self.render_room_sheet(room)
        return HttpResponseRedirect(reverse("room:detail", kwargs={"room_slug": room.slug}))
