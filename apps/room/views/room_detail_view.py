import json

from ambient_toolbox.view_layer import htmx_mixins
from django.db.models import F
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.currency.models import Currency
from apps.debt.models import Debt, NewDebt
from apps.room.models import Room


class RoomDetailView(htmx_mixins.HtmxResponseMixin, generic.DetailView):
    template_name = "room/detail.html"
    context_object_name = "room"
    model = Room
    hx_trigger = {"reloadTransactionList": True}

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
            debts_for_user = Debt.objects.get_debts_for_user_for_room_as_dict_old(user.id, self.object.id)
            if debts_for_user == {}:
                continue

            debts[user.name] = debts_for_user
        return debts

    @context
    @cached_property
    def debt_list(self):
        return Debt.objects.get_debts_for_user_for_room_as_dict(self.object.id)

    @context
    @cached_property
    def new_debts(self):
        return NewDebt.objects.filter_for_room_id(room_id=self.object.id).order_by("settled", "debitor__username")

    def get(self, request, *args, **kwargs):
        ret = super().get(request, *args, **kwargs)

        if not self.request.user.is_anonymous:
            connection = self.object.userconnectiontoroom_set.filter(
                user_id=self.request.user.id, user_has_seen_this_room=False
            ).first()
            if connection is not None:
                connection.user_has_seen_this_room = True
                connection.save()

        return ret
