from django.db.models import F
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.currency.models import Currency
from apps.room.models import UserConnectionToRoom, Room


class TransactionAddModalHTMXView(generic.TemplateView):
    template_name = "transaction/partials/transaction_add_modal.html"

    @context
    @cached_property
    def room_users(self):
        room_slug = self.kwargs.get("slug")
        return (
            UserConnectionToRoom.objects.filter(room__slug=room_slug)
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
    def room(self):
        room_slug = self.kwargs.get("slug")
        return Room.objects.get(slug=room_slug)

    @context
    @cached_property
    def currency_signs(self):
        return Currency.objects.all()
