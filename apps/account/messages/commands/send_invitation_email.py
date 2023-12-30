from dataclasses import dataclass

from apps.account.models import User
from apps.core.event_loop.messages import Command


class SendInvitationEmail(Command):
    @dataclass
    class Context:
        invitee: User
        invitee_email: str
        inviter: User
