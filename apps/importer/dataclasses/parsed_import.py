from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from apps.importer.dataclasses.parsed_category import ParsedCategory
from apps.importer.dataclasses.parsed_settlement import ParsedSettlement
from apps.importer.dataclasses.parsed_transaction import ParsedTransaction
from apps.importer.dataclasses.skipped_row import SkippedRow


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
