from _decimal import Decimal
from dataclasses import dataclass

from apps.account.models import User
from apps.core.event_loop.messages import Command
from apps.room.models import Room


class CreateParentTransaction(Command):
    @dataclass
    class Context:
        room: Room
        value: Decimal
        creditor: User
        debitor: User
