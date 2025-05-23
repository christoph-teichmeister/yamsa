from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.room.models import Room


class RoomCreated(Event):
    @dataclass
    class Context:
        instance: Room
