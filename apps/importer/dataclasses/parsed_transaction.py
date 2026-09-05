from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from apps.importer.dataclasses.parsed_share import ParsedShare


@dataclass(frozen=True)
class ParsedTransaction:
    row_number: int
    paid_at: date
    description: str
    further_notes: str
    category_label: str
    currency_code: str
    payer: str
    shares: tuple[ParsedShare, ...]

    @property
    def total(self) -> Decimal:
        return sum((share.value for share in self.shares), Decimal("0"))

    def as_payload(self) -> dict:
        return {
            "row_number": self.row_number,
            "paid_at": self.paid_at.isoformat(),
            "description": self.description,
            "further_notes": self.further_notes,
            "category_label": self.category_label,
            "currency_code": self.currency_code,
            "payer": self.payer,
            "shares": [share.as_payload() for share in self.shares],
        }

    @classmethod
    def from_payload(cls, payload: dict) -> "ParsedTransaction":
        return cls(
            row_number=payload["row_number"],
            paid_at=date.fromisoformat(payload["paid_at"]),
            description=payload["description"],
            further_notes=payload["further_notes"],
            category_label=payload["category_label"],
            currency_code=payload["currency_code"],
            payer=payload["payer"],
            shares=tuple(ParsedShare.from_payload(entry) for entry in payload["shares"]),
        )
