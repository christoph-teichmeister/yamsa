from decimal import Decimal

from apps.debt.models import Debt
from apps.importer.parsers.splitwise import SplitwiseCsvParser
from apps.importer.tests.factories import build_file_like


class TestImportServiceBalances:
    def test_open_debt_matches_the_export_balance(self, run_import, db, user, currency, parsed):
        # The sample rows net out to 47.77 in favour of Kilian, matching the Gesamtbilanz line.
        result = run_import(parsed=parsed, user=user, currency=currency)

        debt = Debt.objects.get(room=result.room, settled=False)
        assert debt.creditor == user
        assert debt.value == Decimal("47.77")

    def test_settlement_row_becomes_a_settled_debt(self, run_import, db, user, currency):
        parsed = SplitwiseCsvParser().parse(
            build_file_like(
                [
                    "2023-03-06,Ikea,Möbel,100.00,EUR,50.00,-50.00",
                    "2023-04-01,Zahlung,Zahlung,50.00,EUR,-50.00,50.00",
                ]
            )
        )

        result = run_import(parsed=parsed, user=user, currency=currency)

        settled = Debt.objects.get(room=result.room, settled=True)
        assert settled.creditor == user
        assert settled.value == Decimal("50.00")
        assert settled.settled_at.isoformat() == "2023-04-01"
        # The settlement cancels the expense, so nothing is left open.
        assert not Debt.objects.filter(room=result.room, settled=False).exists()
