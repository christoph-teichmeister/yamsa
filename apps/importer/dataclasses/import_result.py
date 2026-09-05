from dataclasses import dataclass


@dataclass(frozen=True)
class ImportResult:
    room: object
    transaction_count: int
    settlement_count: int
    skipped_count: int
    created_category_count: int
    created_guest_count: int
