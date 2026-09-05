from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.room.models import Room


class TransactionsImported(Event):
    @dataclass
    class Context:
        room: Room
        imported_count: int
        settled_count: int
        source_label: str
        triggered_by: object
