from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.currency.models import Currency
from apps.room.forms import RoomCreateForm
from apps.room.models import Room
from apps.room.models import UserConnectionToRoom


class RoomCreateView(generic.CreateView):
    model = Room
    form_class = RoomCreateForm
    template_name = "room/create.html"

    def get_success_url(self):
        return reverse(viewname="room-detail", kwargs={"room_slug": self.object.slug})

    @context
    @cached_property
    def currencies(self):
        return Currency.objects.all()

    def form_valid(self, form):
        created_room: Room = form.instance

        created_room.created_at = timezone.now()
        created_room.created_by = self.request.user

        ret = super().form_valid(form)

        UserConnectionToRoom.objects.create(user=self.request.user, room=created_room)

        return ret
