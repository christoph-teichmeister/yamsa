from django.urls import reverse
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.room.forms.room_edit_form import RoomEditForm
from apps.room.models import Room
from apps.room.views.mixins.room_base_context import RoomBaseContext


class RoomEditView(RoomBaseContext, generic.UpdateView):
    template_name = "room/edit.html"
    slug_url_kwarg = "room_slug"
    model = Room
    form_class = RoomEditForm

    def get_success_url(self):
        return reverse("room-edit", kwargs={"room_slug": self.object.slug})

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # Add user to form
        setattr(form, "user", self.request.user)

        return form

    @context
    @cached_property
    def other_status(self):
        return list(
            filter(lambda choice_option: choice_option != self.object.status, self.object.StatusChoices.values)
        )[0]
