from django.urls import reverse

from apps.room.dataclasses import DashboardTab

from apps.room.models import Room


class DashboardTabService:
    room: Room

    def __init__(self, room: Room):
        self.room = room

    def get_tabs_as_list(self) -> list[DashboardTab]:
        return [
            DashboardTab(
                name="transaction",
                icon_class="bi bi-wallet",
                room=self.room,
                get_url=reverse("transaction-list", kwargs={"room_slug": self.room.slug}),
            ),
            DashboardTab(
                name="debt",
                icon_class="bi bi-piggy-bank",
                room=self.room,
                get_url=reverse("debt-list", kwargs={"room_slug": self.room.slug}),
            ),
            DashboardTab(name="people", icon_class="bi bi-people", room=self.room),
            DashboardTab(name="settings", icon_class="bi bi-gear", room=self.room),
        ]
