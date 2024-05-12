from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.room.models import UserConnectionToRoom


class UserConnectionToRoomCreated(Event):
    @dataclass
    class Context:
        instance: UserConnectionToRoom
