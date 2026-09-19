from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View

from apps.room.forms import RoomSealIconForm
from apps.room.views.mixins.room_sheet_response import RoomSheetResponseMixin


class RoomSealIconUpdateView(RoomSheetResponseMixin, View):
    """Pick one of the predefined seal icons, replacing any custom image."""

    def post(self, request, *args, **kwargs):
        room = request.room
        form = RoomSealIconForm(request.POST, instance=room)

        if not form.is_valid():
            if self.is_htmx_request():
                return self.render_room_sheet(room, seal_form=form, seal_dialog_is_open=True)
            return HttpResponseRedirect(reverse("room:detail", kwargs={"room_slug": room.slug}))

        room = form.save()

        if self.is_htmx_request():
            return self.render_room_sheet(room)
        return HttpResponseRedirect(reverse("room:detail", kwargs={"room_slug": room.slug}))
