from dataclasses import dataclass


@dataclass(frozen=True)
class SkippedRow:
    row_number: int
    reason: str
    excerpt: str

    def as_payload(self) -> dict:
        return {"row_number": self.row_number, "reason": self.reason, "excerpt": self.excerpt}

    @classmethod
    def from_payload(cls, payload: dict) -> "SkippedRow":
        return cls(row_number=payload["row_number"], reason=payload["reason"], excerpt=payload["excerpt"])
