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

        return Room.objects.filter(created_by=user)


class RoomDetailView(generic.DetailView):
    template_name = "room/detail.html"
    context_object_name = "room"
    model = Room

    def get_context_data(self, **kwargs) -> dict:
        context_data = super().get_context_data(**kwargs)

        room = context_data.get("room")
        room_users = room.users.all().values("name", "id")

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
        )

        debts = DebtService.get_debts_dict(room_transactions_qs=room_transactions_qs)

        queries_before_tuple = len(connection.queries)
        start = time.time()
        money_flow_tuple = DebtService.build_money_flow_tuple(
            queryset=room_transactions_qs
        )
        queries_after_tuple = len(connection.queries)
        end = time.time()
        print(
            f"money_flow_tuple took {end - start} and made {queries_after_tuple - queries_before_tuple} queries\n"
        )

        queries_before_qs = len(connection.queries)
        start = time.time()
        money_flow_qs = DebtService.build_money_flow_queryset(
            queryset=room_transactions_qs
        )
        queries_after_qs = len(connection.queries)
        end = time.time()
        print(
            f"money_flow_qs took {end - start}and made {queries_after_qs - queries_before_qs} queries\n"
        )

        # money_flow_qs = MoneyFlow.objects.try_to_resolve_flows_and_reduce_them_to_zero(
        #     room_id=room.id
        # )

        return {
            **context_data,
            "room_users": room_users,
            "room_transactions": room_transactions,
            "debts": debts,
            "money_flow_tuple": money_flow_tuple,
            "money_flow_qs": money_flow_qs,
            "shit_qs": money_flow_qs,
        }
