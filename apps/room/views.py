from django.db.models import F
from django.http import HttpResponse
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

        room_transactions_qs = room.transactions.all()
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
        money_flow_tuple = DebtService.build_money_flow_tuple(
            queryset=room_transactions_qs
        )

        return {
            **context_data,
            "room_users": room_users,
            "room_transactions": room_transactions,
            "debts": debts,
            "optimised_debts": money_flow_tuple,
        }

    def post(self, *args, **kwargs):
        print("POSTED")
        return HttpResponse(status=200)
