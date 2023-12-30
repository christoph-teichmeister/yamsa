from dataclasses import dataclass

from apps.account.models import User
from apps.core.event_loop.messages import Event


class PostRegisterEmailSent(Event):
    @dataclass
    class Context:
        user: User
