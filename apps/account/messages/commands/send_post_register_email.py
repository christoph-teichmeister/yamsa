from dataclasses import dataclass

from apps.account.models import User
from apps.core.event_loop.messages import Command


class SendPostRegisterEmail(Command):
    @dataclass
    class Context:
        user: User
