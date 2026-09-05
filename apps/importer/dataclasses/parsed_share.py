from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ParsedShare:
    person: str
    value: Decimal

    def as_payload(self) -> dict:
        return {"person": self.person, "value": str(self.value)}

    @classmethod
    def from_payload(cls, payload: dict) -> "ParsedShare":
        return cls(person=payload["person"], value=Decimal(payload["value"]))
