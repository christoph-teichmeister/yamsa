from dataclasses import dataclass

from apps.account.models import User
from apps.core.event_loop.messages import Event


class InvitationEmailSent(Event):
    @dataclass
    class Context:
        invitee: User
        invitee_email: str
        inviter: User
