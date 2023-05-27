from django.db.models import F
from django.views import generic

from apps.core.context_managers import measure_time_and_queries
from apps.debt.models import Debt
from apps.room.models import Room


class RoomDetailView(generic.DetailView):
    template_name = "room/detail.html"
    context_object_name = "room"
    model = Room

    @measure_time_and_queries("RoomDetailView.get_context_data()")
    def get_context_data(self, **kwargs) -> dict:
        context_data = super().get_context_data(**kwargs)

        room = context_data.get("room")
        room_users = (
            room.userconnectiontoroom_set.all()
            .values("user_has_seen_this_room")
            .annotate(
                name=F("user__name"),
                id=F("user__id"),
                is_guest=F("user__is_guest"),
            )
            .order_by("user_has_seen_this_room", "name")
        )

        room_transactions = (
            room.transactions.all()
            .select_related("paid_by", "room")
            .prefetch_related("paid_for")
            .annotate(
                paid_by_name=F("paid_by__name"),
                paid_for_name=F("paid_for__name"),
            )
            .values(
                "id",
                "description",
                "value",
                "paid_by_name",
                "paid_for_name",
                "created_at",
            )
        )

        debts = {}
        for user in room.users.all().order_by("name"):
            debts_for_user = Debt.objects.get_debts_for_user_for_room_as_dict(
                user.id, room.id
            )
            if debts_for_user == {}:
                continue

            debts[user.name] = debts_for_user

        return {
            **context_data,
            "room_users": room_users,
            "room_transactions": room_transactions,
            "debts": debts,
            "money_flow_qs": room.money_flows.all(),
        }
