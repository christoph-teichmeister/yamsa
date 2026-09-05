import csv
import io
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from django.utils.translation import gettext as _

from apps.importer.dataclasses import (
    ParsedCategory,
    ParsedImport,
    ParsedSettlement,
    ParsedShare,
    ParsedTransaction,
    SkippedRow,
)
from apps.importer.parsers.base import MAX_IMPORT_ROWS, BaseImportParser
from apps.importer.parsers.exceptions import ImportParseError
from apps.transaction.models import DEFAULT_CATEGORY_SLUG

# Splitwise puts five fixed columns first; everything after them is one column per person.
FIXED_COLUMN_COUNT = 5

# Net values of a row must cancel out. Splitwise rounds to cents, so allow one cent of drift.
BALANCE_TOLERANCE = Decimal("0.01")

# Settlements carry this category instead of a real one; the label follows the account language.
PAYMENT_CATEGORY_LABELS = frozenset({"zahlung", "payment"})

CATEGORY_SLUG_BY_LABEL = {
    "allgemein": DEFAULT_CATEGORY_SLUG,
    "general": DEFAULT_CATEGORY_SLUG,
    "sonstiges": DEFAULT_CATEGORY_SLUG,
    "lebensmittel": "groceries",
    "groceries": "groceries",
    "restaurant": "restaurants-and-bars",
    "dining out": "restaurants-and-bars",
    "getränke": "restaurants-and-bars",
    "auto": "transport",
    "treibstoff": "transport",
    "parken": "transport",
    "bus/bahn": "transport",
    "taxi": "transport",
    "möbel": "household",
    "zuhause - sonstiges": "household",
    "haushaltsartikel": "household",
    "elektronik": "household",
    "kleidung": "shopping",
    "medikamente": "health",
    "arzt": "health",
    "geschenke": "celebrations",
    "kino": "activities",
    "sport": "activities",
    "spiele": "activities",
    "unterhaltung": "activities",
    "miete": "accommodation",
    "unterkunft": "accommodation",
    "hotel": "accommodation",
}

FALLBACK_EMOJI = "🏷️"
EMOJI_BY_LABEL = {
    "möbel": "🛋️",
    "treibstoff": "⛽",
    "parken": "🅿️",
    "kino": "🎬",
    "auto": "🚗",
    "kleidung": "👕",
    "medikamente": "💊",
    "geschenke": "🎁",
    "lebensmittel": "🛒",
    "restaurant": "🍽️",
    "zuhause - sonstiges": "🏠",
    "sport": "⚽",
    "spiele": "🎲",
    "unterhaltung": "🎉",
}

DECIMAL_DOT_PATTERN = re.compile(r"^-?\d+(\.\d+)?$")
DECIMAL_COMMA_PATTERN = re.compile(r"^-?\d+,\d+$")

# ParentTransaction.description is capped at 50 characters; the untruncated text goes to further_notes.
MAX_DESCRIPTION_LENGTH = 50


class SplitwiseCsvParser(BaseImportParser):
    source_key = "splitwise-csv"
    label = "Splitwise (CSV)"

    def parse(self, uploaded_file) -> ParsedImport:
        rows = self._read_rows(uploaded_file)
        if not rows:
            raise ImportParseError(_("The file is empty."))

        people = self._read_people(rows[0])

        transactions: list[ParsedTransaction] = []
        settlements: list[ParsedSettlement] = []
        skipped: list[SkippedRow] = []

        data_rows = rows[1:]
        if len(data_rows) > MAX_IMPORT_ROWS:
            raise ImportParseError(
                _("The file has %(count)d rows, the import handles at most %(limit)d.")
                % {"count": len(data_rows), "limit": MAX_IMPORT_ROWS}
            )

        for offset, row in enumerate(data_rows):
            # Row 1 is the header, so the first data row is number 2 — matching what a spreadsheet shows.
            row_number = offset + 2
            if not any(cell.strip() for cell in row):
                continue
            self._handle_row(row, row_number, people, transactions, settlements, skipped)

        return ParsedImport(
            source_key=self.source_key,
            people=people,
            transactions=tuple(transactions),
            settlements=tuple(settlements),
            skipped_rows=tuple(skipped),
            categories=self._collect_categories(transactions),
        )

    def _read_rows(self, uploaded_file) -> list[list[str]]:
        raw = uploaded_file.read()
        if isinstance(raw, bytes):
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError as error:
                raise ImportParseError(_("The file is not valid UTF-8 text.")) from error
        else:
            text = raw
        return list(csv.reader(io.StringIO(text)))

    def _read_people(self, header: list[str]) -> tuple[str, ...]:
        people = tuple(name.strip() for name in header[FIXED_COLUMN_COUNT:] if name.strip())
        if not people:
            raise ImportParseError(
                _("No person columns found. A Splitwise export has one column per person after the currency column.")
            )
        return people

    def _handle_row(
        self,
        row: list[str],
        row_number: int,
        people: tuple[str, ...],
        transactions: list[ParsedTransaction],
        settlements: list[ParsedSettlement],
        skipped: list[SkippedRow],
    ) -> None:
        def skip(reason: str) -> None:
            skipped.append(SkippedRow(row_number=row_number, reason=reason, excerpt=self._excerpt(row)))

        cells = [cell.strip() for cell in row]
        cells += [""] * (FIXED_COLUMN_COUNT + len(people) - len(cells))

        raw_date, raw_description, raw_category, raw_cost, raw_currency = cells[:FIXED_COLUMN_COUNT]

        if not raw_cost:
            # The Splitwise export ends with a "Gesamtbilanz" summary row that has no cost.
            skip(_("Row without a cost value (e.g. the balance summary line)"))
            return

        paid_at = self._parse_date(raw_date)
        if paid_at is None:
            skip(_("Unreadable date '%(value)s'") % {"value": raw_date})
            return

        cost = self._parse_decimal(raw_cost)
        if cost is None:
            skip(_("Unreadable cost '%(value)s'") % {"value": raw_cost})
            return

        nets: list[Decimal] = []
        for index, person in enumerate(people):
            value = self._parse_decimal(cells[FIXED_COLUMN_COUNT + index] or "0")
            if value is None:
                skip(_("Unreadable value for %(person)s") % {"person": person})
                return
            nets.append(value)

        if abs(sum(nets, Decimal("0"))) > BALANCE_TOLERANCE:
            skip(_("The person columns do not cancel out"))
            return

        if raw_category.strip().lower() in PAYMENT_CATEGORY_LABELS:
            self._handle_settlement(
                people=people,
                nets=nets,
                cost=cost,
                settled_at=paid_at,
                currency_code=raw_currency,
                row_number=row_number,
                settlements=settlements,
                skip=skip,
            )
            return

        if cost <= 0:
            skip(_("Cost is zero"))
            return

        payer_indexes = [index for index, value in enumerate(nets) if value > 0]
        if not payer_indexes:
            skip(_("No payer — everybody covered their own share"))
            return
        if len(payer_indexes) > 1:
            skip(_("More than one payer, which a single transaction cannot represent"))
            return

        payer_index = payer_indexes[0]
        shares = self._build_shares(people=people, nets=nets, cost=cost, payer_index=payer_index)
        if shares is None:
            skip(_("The shares do not add up to the cost"))
            return

        transactions.append(
            ParsedTransaction(
                row_number=row_number,
                paid_at=paid_at,
                description=raw_description[:MAX_DESCRIPTION_LENGTH] or _("Import"),
                further_notes=raw_description if len(raw_description) > MAX_DESCRIPTION_LENGTH else "",
                category_label=raw_category,
                currency_code=raw_currency,
                payer=people[payer_index],
                shares=shares,
            )
        )

    def _handle_settlement(
        self,
        *,
        people: tuple[str, ...],
        nets: list[Decimal],
        cost: Decimal,
        settled_at: date,
        currency_code: str,
        row_number: int,
        settlements: list[ParsedSettlement],
        skip,
    ) -> None:
        positives = [index for index, value in enumerate(nets) if value > 0]
        negatives = [index for index, value in enumerate(nets) if value < 0]
        if len(positives) != 1 or len(negatives) != 1:
            skip(_("A settlement needs exactly one payer and one recipient"))
            return
        if cost <= 0:
            skip(_("Settlement without an amount"))
            return

        settlements.append(
            ParsedSettlement(
                row_number=row_number,
                settled_at=settled_at,
                # The person who transferred the money owed it, so they are the debitor.
                debitor=people[positives[0]],
                creditor=people[negatives[0]],
                value=cost,
                currency_code=currency_code,
            )
        )

    def _build_shares(
        self, *, people: tuple[str, ...], nets: list[Decimal], cost: Decimal, payer_index: int
    ) -> tuple[ParsedShare, ...] | None:
        shares: list[ParsedShare] = []
        others_total = Decimal("0")
        for index, person in enumerate(people):
            if index == payer_index:
                continue
            share = -nets[index]
            if share < 0:
                return None
            others_total += share
            if share > 0:
                shares.append(ParsedShare(person=person, value=share))

        payer_share = cost - others_total
        if payer_share < 0:
            return None
        if payer_share > 0:
            shares.insert(0, ParsedShare(person=people[payer_index], value=payer_share))

        if not shares:
            return None
        return tuple(shares)

    def _collect_categories(self, transactions: list[ParsedTransaction]) -> tuple[ParsedCategory, ...]:
        counts: dict[str, int] = {}
        for transaction in transactions:
            label = transaction.category_label
            counts[label] = counts.get(label, 0) + 1

        return tuple(
            ParsedCategory(
                label=label,
                suggested_slug=self.map_category_slug(label),
                suggested_emoji=self.suggest_emoji(label),
                transaction_count=count,
            )
            for label, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        )

    @staticmethod
    def map_category_slug(label: str) -> str:
        return CATEGORY_SLUG_BY_LABEL.get(label.strip().lower(), DEFAULT_CATEGORY_SLUG)

    @staticmethod
    def suggest_emoji(label: str) -> str:
        return EMOJI_BY_LABEL.get(label.strip().lower(), FALLBACK_EMOJI)

    @staticmethod
    def _parse_date(value: str) -> date | None:
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            return None

    @staticmethod
    def _parse_decimal(value: str) -> Decimal | None:
        candidate = value.strip()
        if not candidate:
            return Decimal("0")
        if DECIMAL_COMMA_PATTERN.match(candidate):
            candidate = candidate.replace(",", ".")
        if not DECIMAL_DOT_PATTERN.match(candidate):
            return None
        try:
            return Decimal(candidate)
        except InvalidOperation:
            return None

    @staticmethod
    def _excerpt(row: list[str]) -> str:
        return ", ".join(cell.strip() for cell in row if cell.strip())[:120]
