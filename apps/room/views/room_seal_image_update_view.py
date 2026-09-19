from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View

from apps.room.forms import RoomSealImageForm
from apps.room.views.mixins.room_sheet_response import RoomSheetResponseMixin


class RoomSealImageUpdateView(RoomSheetResponseMixin, View):
    """Upload a custom seal image, replacing any predefined icon choice."""

    def post(self, request, *args, **kwargs):
        room = request.room
        form = RoomSealImageForm(request.POST, request.FILES, instance=room)

        if not form.is_valid():
            if self.is_htmx_request():
                return self.render_room_sheet(room, seal_form=form, seal_dialog_is_open=True)
            return HttpResponseRedirect(reverse("room:detail", kwargs={"room_slug": room.slug}))

        room = form.save()

        if self.is_htmx_request():
            return self.render_room_sheet(room)
        return HttpResponseRedirect(reverse("room:detail", kwargs={"room_slug": room.slug}))
