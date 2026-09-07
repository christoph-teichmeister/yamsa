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
                icon_name="wallet",
                room=self.room,
                get_url=reverse("transaction:list", kwargs={"room_slug": self.room.slug}),
            ),
            DashboardTab(
                name="debt",
                icon_name="piggy-bank",
                room=self.room,
                get_url=reverse("debt:list", kwargs={"room_slug": self.room.slug}),
            ),
            DashboardTab(
                name="people",
                icon_name="people",
                room=self.room,
                get_url=reverse("account:list", kwargs={"room_slug": self.room.slug}),
            ),
            DashboardTab(
                name="room",
                icon_name="gear",
                room=self.room,
                get_url=reverse("room:detail", kwargs={"room_slug": self.room.slug}),
            ),
        ]
