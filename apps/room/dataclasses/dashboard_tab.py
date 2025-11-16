from dataclasses import dataclass

from django.urls import reverse

from apps.room.models import Room


@dataclass
class DashboardTab:
    name: str
    get_url: str
    icon_class: str

    def __init__(self, name: str, icon_class: str, room: Room, get_url: str | None = None):
        super().__init__()

        self.name = name
        self.icon_class = icon_class

        if get_url is None:
            get_url = f"{reverse('room:dashboard', kwargs={'room_slug': room.slug})}?active_tab={name}"

        self.get_url = get_url
