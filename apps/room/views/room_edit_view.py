from django.urls import reverse
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.room.forms import RoomEditForm
from apps.room.models import Room
from apps.room.views.mixins.room_base_context import RoomBaseContext
from apps.room.views.mixins.room_sheet_response import RoomSheetResponseMixin


class RoomEditView(RoomSheetResponseMixin, RoomBaseContext, generic.UpdateView):
    # The room is one page that switches between reading and editing in place, so this view
    # renders the very same template — only with the sheet unlocked. A plain GET landing here is
    # what carries editing without the bundle.
    template_name = "room/detail.html"
    context_object_name = "room"
    slug_url_kwarg = "room_slug"
    model = Room
    form_class = RoomEditForm

    def get_success_url(self):
        return reverse("room:detail", kwargs={"room_slug": self.object.slug})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.user = self.request.user
        return form

    @context
    @cached_property
    def room_is_editing(self):
        return True

    @context
    @cached_property
    def open_debt_count(self):
        return self.object.debts.filter(settled=False).count()

    def form_valid(self, form):
        response = super().form_valid(form)

        if not self.is_htmx_request():
            return response

        return self.render_room_sheet(self.object, is_editing=False)

    def form_invalid(self, form):
        if self.is_htmx_request():
            return self.render_room_sheet(self.object, is_editing=True, form=form)
        return super().form_invalid(form)
