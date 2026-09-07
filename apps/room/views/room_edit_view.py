from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.room.forms import RoomEditForm
from apps.room.models import Room
from apps.room.views.mixins.room_base_context import RoomBaseContext
from apps.room.views.mixins.room_sheet_response import RoomSheetResponseMixin


class RoomEditView(RoomSheetResponseMixin, RoomBaseContext, generic.UpdateView):
    # The sheet is editable wherever it is shown, so this view has no page of its own: it is the
    # POST target, and a GET on it belongs on the room.
    template_name = "room/detail.html"
    context_object_name = "room"
    slug_url_kwarg = "room_slug"
    model = Room
    form_class = RoomEditForm

    def get(self, request, *args, **kwargs):
        return redirect("room:detail", room_slug=kwargs[self.slug_url_kwarg])

    def get_success_url(self):
        return reverse("room:detail", kwargs={"room_slug": self.object.slug})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.user = self.request.user
        return form

    @context
    @cached_property
    def open_debt_count(self):
        return self.object.debts.filter(settled=False).count()

    def form_valid(self, form):
        response = super().form_valid(form)

        if not self.is_htmx_request():
            return response

        return self.render_room_sheet(self.object)

    def form_invalid(self, form):
        if self.is_htmx_request():
            return self.render_room_sheet(self.object, form=form)
        return super().form_invalid(form)
