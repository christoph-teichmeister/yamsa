from dataclasses import dataclass, field

from apps.room.models import Room


@dataclass(frozen=True)
class ImportResult:
    room: Room
    transaction_count: int
    settlement_count: int
    skipped_count: int
    created_category_count: int
    created_guest_count: int
    # Users whose room connection must be created after the atomic block, because saving it
    # emits webpush and email synchronously.
    deferred_connections: list = field(default_factory=list)
