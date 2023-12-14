from django.urls import reverse
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.room.forms.room_edit_form import RoomEditForm
from apps.room.models import Room


class RoomEditView(generic.UpdateView):
    template_name = "room/edit.html"
    slug_url_kwarg = "room_slug"
    model = Room
    form_class = RoomEditForm

    # TODO CT: Disable quite a few things when a room is closed!

    def get_success_url(self):
        return reverse("room-edit", kwargs={"room_slug": self.object.slug})

    @context
    @cached_property
    def other_status(self):
        return list(
            filter(lambda choice_option: choice_option != self.object.status, self.object.StatusChoices.values)
        )[0]

    @context
    @cached_property
    def active_tab(self):
        return self.request.GET.get("active_tab", "settings")
