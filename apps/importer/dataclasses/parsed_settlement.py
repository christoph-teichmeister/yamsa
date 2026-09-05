from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class ParsedSettlement:
    row_number: int
    settled_at: date
    debitor: str
    creditor: str
    value: Decimal
    currency_code: str

    def as_payload(self) -> dict:
        return {
            "row_number": self.row_number,
            "settled_at": self.settled_at.isoformat(),
            "debitor": self.debitor,
            "creditor": self.creditor,
            "value": str(self.value),
            "currency_code": self.currency_code,
        }

    @classmethod
    def from_payload(cls, payload: dict) -> "ParsedSettlement":
        return cls(
            row_number=payload["row_number"],
            settled_at=date.fromisoformat(payload["settled_at"]),
            debitor=payload["debitor"],
            creditor=payload["creditor"],
            value=Decimal(payload["value"]),
            currency_code=payload["currency_code"],
        )
