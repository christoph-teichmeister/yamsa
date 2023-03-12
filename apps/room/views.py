from django.db.models import F
from django.http import HttpResponse
from django.views import generic

from apps.room.models import Room


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
        room_transactions = (
            room.transactions.all()
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
            )
        )

        return {
            **context_data,
            "room_users": room_users,
            "room_transactions": room_transactions,
        }

    def post(self, *args, **kwargs):
        print("POSTED")
        return HttpResponse(status=200)
