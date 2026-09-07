from django.urls import reverse
from django.utils import timezone
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.room.forms import RoomStatusForm
from apps.room.messages.events.room_status_changed import RoomStatusChanged
from apps.room.models import Room
from apps.room.views.mixins.room_base_context import RoomBaseContext
from apps.room.views.mixins.room_sheet_response import RoomSheetResponseMixin


class RoomStatusUpdateView(RoomSheetResponseMixin, RoomBaseContext, generic.UpdateView):
    # Answers with the sheet, never with a page of its own: closing a room changes its badge, its
    # readiness row and whether its fields can be edited at all, so the whole sheet comes back.
    template_name = "room/detail.html"
    context_object_name = "room"
    slug_url_kwarg = "room_slug"
    model = Room
    form_class = RoomStatusForm

    def get_success_url(self):
        return reverse("room:detail", kwargs={"room_slug": self.object.slug})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.user = self.request.user
        return form

    def form_valid(self, form):
        status_changed = "status" in form.changed_data
        force_closed = form.closes_the_room and form.cleaned_data.get("force_close")

        response = super().form_valid(form)

        # Both of these are side effects rather than persistence of the room itself, so they sit
        # here and not in the form's save() — see AGENTS.md § Hard rules.
        if force_closed:
            self.object.debts.filter(settled=False).update(settled=True, settled_at=timezone.localdate())

        if status_changed:
            handle_message(RoomStatusChanged(context_data={"room": self.object}))

        if not self.is_htmx_request():
            return response

        return self.render_room_sheet(self.object)

    def form_invalid(self, form):
        if self.is_htmx_request():
            return self.render_room_sheet(self.object, status_form=form)
        return super().form_invalid(form)
