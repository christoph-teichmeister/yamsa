from dataclasses import dataclass

from apps.account.models import User
from apps.core.event_loop.messages import Command
from apps.room.models import Room


class RemoveUserFromRoom(Command):
    @dataclass
    class Context:
        room: Room
        user_to_be_removed: User
        user_requesting_removal: User
