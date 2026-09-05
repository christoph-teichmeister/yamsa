from dataclasses import dataclass
from datetime import date
from decimal import Decimal

# The parsed representation is handed to the preview form and back through the session,
# so every dataclass here must survive a JSON round-trip via as_payload()/from_payload().


@dataclass(frozen=True)
class ParsedShare:
    person: str
    value: Decimal

    def as_payload(self) -> dict:
        return {"person": self.person, "value": str(self.value)}

    @classmethod
    def from_payload(cls, payload: dict) -> "ParsedShare":
        return cls(person=payload["person"], value=Decimal(payload["value"]))


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


@dataclass(frozen=True)
class ParsedImport:
    source_key: str
    people: tuple[str, ...]
    transactions: tuple[ParsedTransaction, ...]
    settlements: tuple[ParsedSettlement, ...]
    skipped_rows: tuple[SkippedRow, ...]
    categories: tuple[ParsedCategory, ...]

    @property
    def currency_codes(self) -> list[str]:
        """Currency codes in the file, most frequent first."""
        counts: dict[str, int] = {}
        for transaction in self.transactions:
            counts[transaction.currency_code] = counts.get(transaction.currency_code, 0) + 1
        for settlement in self.settlements:
            counts[settlement.currency_code] = counts.get(settlement.currency_code, 0) + 1
        return [code for code, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]

    @property
    def date_range(self) -> tuple[date, date] | None:
        dates = [transaction.paid_at for transaction in self.transactions]
        dates += [settlement.settled_at for settlement in self.settlements]
        if not dates:
            return None
        return min(dates), max(dates)

    def totals_by_currency(self) -> dict[str, Decimal]:
        totals: dict[str, Decimal] = {}
        for transaction in self.transactions:
            totals[transaction.currency_code] = totals.get(transaction.currency_code, Decimal("0")) + transaction.total
        return totals

    def as_payload(self) -> dict:
        return {
            "source_key": self.source_key,
            "people": list(self.people),
            "transactions": [entry.as_payload() for entry in self.transactions],
            "settlements": [entry.as_payload() for entry in self.settlements],
            "skipped_rows": [entry.as_payload() for entry in self.skipped_rows],
            "categories": [entry.as_payload() for entry in self.categories],
        }

    @classmethod
    def from_payload(cls, payload: dict) -> "ParsedImport":
        return cls(
            source_key=payload["source_key"],
            people=tuple(payload["people"]),
            transactions=tuple(ParsedTransaction.from_payload(entry) for entry in payload["transactions"]),
            settlements=tuple(ParsedSettlement.from_payload(entry) for entry in payload["settlements"]),
            skipped_rows=tuple(SkippedRow.from_payload(entry) for entry in payload["skipped_rows"]),
            categories=tuple(ParsedCategory.from_payload(entry) for entry in payload["categories"]),
        )


@dataclass(frozen=True)
class PersonAssignment:
    """How one person column of the file maps onto a yamsa user."""

    ME = "me"
    EXISTING = "existing"
    GUEST = "guest"

    column: str
    kind: str
    user_id: int | None = None
    guest_name: str = ""


@dataclass(frozen=True)
class CategoryAssignment:
    """How one source category maps onto a room category."""

    EXISTING = "existing"
    NEW = "new"

    label: str
    kind: str
    slug: str = ""
    name: str = ""
    emoji: str = ""


@dataclass(frozen=True)
class ImportResult:
    room: object
    transaction_count: int
    settlement_count: int
    skipped_count: int
    created_category_count: int
    created_guest_count: int
