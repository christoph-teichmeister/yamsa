from dataclasses import dataclass

from apps.account.models import User
from apps.core.event_loop.messages import Command
from apps.room.models import Room


class DeleteRoom(Command):
    @dataclass
    class Context:
        room: Room
        user_requesting_deletion: User
