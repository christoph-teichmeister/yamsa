from django.db.models import F
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.currency.models import Currency
from apps.room.models import UserConnectionToRoom
from apps.room.views.mixins.room_specific_mixin import RoomSpecificMixin


class GetTransactionAddModalHTMXView(RoomSpecificMixin, generic.TemplateView):
    template_name = "transaction/partials/transaction_add_modal.html"

    @context
    @cached_property
    def room_users(self):
        # TODO CT: why is this done (look at room_users of RoomSpecificMixin
        return (
            UserConnectionToRoom.objects.filter(room__slug=self._room.slug)
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
    def currency_signs(self):
        return Currency.objects.all()
