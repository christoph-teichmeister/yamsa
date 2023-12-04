from django.db.models import F
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.currency.models import Currency
from apps.room.models import Room


class RoomDetailView(generic.DetailView):
    template_name = "room/detail.html"
    context_object_name = "room"
    slug_url_kwarg = "room_slug"
    model = Room

    @context
    @cached_property
    def room_users(self):
        return (
            self.object.userconnectiontoroom_set.all()
            .select_related("user")
            .values("user_has_seen_this_room")
            .annotate(
                name=F("user__name"),
                id=F("user__id"),
                is_guest=F("user__is_guest"),
            )
            .order_by("user_has_seen_this_room", "name")
        )

    @context
    @cached_property
    def preferred_currency_sign(self):
        return self.object.preferred_currency.sign

    @context
    @cached_property
    def currency_signs(self):
        return Currency.objects.all()

    @context
    @cached_property
    def active_tab(self):
        return self.request.GET.get("active_tab", "settings")
