from django.db.models import F
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.currency.models import Currency
from apps.debt.models import Debt
from apps.room.models import Room


class RoomDetailView(generic.DetailView):
    template_name = "room/detail.html"
    context_object_name = "room"
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
    def debts(self):
        debts = {}
        for user in self.object.users.all().order_by("name"):
            debts_for_user = Debt.objects.get_debts_for_user_for_room_as_dict(
                user.id, self.object.id
            )
            if debts_for_user == {}:
                continue

            debts[user.name] = debts_for_user
        return debts

    @context
    @cached_property
    def money_flow_qs(self):
        return self.object.money_flows.all()

    def get(self, request, *args, **kwargs):
        ret = super().get(request, *args, **kwargs)
        ret.headers["HX-Trigger-After-Swap"] = "reloadTransactionList"

        if not self.request.user.is_anonymous:
            connection = self.object.userconnectiontoroom_set.filter(
                user_id=self.request.user.id, user_has_seen_this_room=False
            ).first()
            if connection is not None:
                connection.user_has_seen_this_room = True
                connection.save()

        return ret
