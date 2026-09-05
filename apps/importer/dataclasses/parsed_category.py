from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedCategory:
    label: str
    suggested_slug: str
    suggested_emoji: str
    transaction_count: int

    def as_payload(self) -> dict:
        return {
            "label": self.label,
            "suggested_slug": self.suggested_slug,
            "suggested_emoji": self.suggested_emoji,
            "transaction_count": self.transaction_count,
        }

    @classmethod
    def from_payload(cls, payload: dict) -> "ParsedCategory":
        return cls(
            label=payload["label"],
            suggested_slug=payload["suggested_slug"],
            suggested_emoji=payload["suggested_emoji"],
            transaction_count=payload["transaction_count"],
        )
