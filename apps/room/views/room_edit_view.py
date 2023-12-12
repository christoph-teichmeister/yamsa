from django.urls import reverse
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.currency.models import Currency
from apps.room.models import Room


class RoomEditView(generic.UpdateView):
    template_name = "room/edit.html"
    context_object_name = "room"
    slug_url_kwarg = "room_slug"
    model = Room
    fields = ("name", "description", "preferred_currency")

    def get_success_url(self):
        return reverse("room-edit", kwargs={"room_slug": self.object.slug})

    @context
    @cached_property
    def currencies(self):
        return Currency.objects.all()

    @context
    @cached_property
    def active_tab(self):
        return self.request.GET.get("active_tab", "settings")
