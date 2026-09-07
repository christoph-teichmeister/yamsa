from dataclasses import dataclass

from django.urls import reverse

from apps.room.models import Room


@dataclass
class DashboardTab:
    name: str
    get_url: str
    icon_name: str

    def __init__(self, name: str, icon_name: str, room: Room, get_url: str | None = None):
        super().__init__()

        self.name = name
        self.icon_name = icon_name

        if get_url is None:
            get_url = f"{reverse('room:dashboard', kwargs={'room_slug': room.slug})}?active_tab={name}"

        self.get_url = get_url
