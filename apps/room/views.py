import time

from django.db import connection
from django.db.models import F
from django.views import generic

from apps.room.models import Room
from apps.transaction.services import DebtService


class RoomListView(generic.ListView):
    template_name = "room/list.html"
    context_object_name = "rooms"
    model = Room

    def get_queryset(self):
        user = self.request.user

        if user.is_anonymous:
            return Room.objects.none()

        if user.is_superuser:
            return Room.objects.all()

        return Room.objects.filter(users=user)


class RoomDetailView(generic.DetailView):
    template_name = "room/detail.html"
    context_object_name = "room"
    model = Room

    def get_context_data(self, **kwargs) -> dict:
        context_data = super().get_context_data(**kwargs)

        room = context_data.get("room")
        room_users = room.users.all().values("name", "id", "is_guest")

        room_transactions_qs = (
            room.transactions.all()
            .select_related("paid_by", "room")
            .prefetch_related("paid_for")
        )
        room_transactions = room_transactions_qs.annotate(
            paid_by_name=F("paid_by__name"), paid_for_name=F("paid_for__name")
        ).values(
            "id",
            "description",
            "value",
            "paid_by_name",
            "paid_for_name",
            "created_at",
        )

        queries_before_qs = len(connection.queries)
        start = time.time()

        money_flow_qs = room.money_flows.all()

        queries_after_qs = len(connection.queries)
        end = time.time()
        print(
            f"money_flow_qs took {end - start} seconds and made {queries_after_qs - queries_before_qs} queries\n"
        )

        return {
            **context_data,
            "room_users": room_users,
            "room_transactions": room_transactions,
            "debts": DebtService.get_debts_dict(
                room_transactions_qs=room_transactions_qs.filter(settled=False)
            ),
            "money_flow_qs": money_flow_qs,
        }
