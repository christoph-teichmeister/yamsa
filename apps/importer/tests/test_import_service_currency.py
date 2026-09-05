from apps.currency.models import Currency
from apps.importer.parsers.splitwise import SplitwiseCsvParser
from apps.importer.tests.factories import build_file_like
from apps.transaction.models import ParentTransaction


class TestImportServiceCurrency:
    def test_duplicate_currency_codes_do_not_break_the_import(self, run_import, db, user, currency, parsed):
        # Currency.code has no unique constraint, so a .get() would raise MultipleObjectsReturned.
        Currency.objects.create(name="Euro (duplicate)", sign="€", code="EUR")

        result = run_import(parsed=parsed, user=user, currency=currency)

        assert ParentTransaction.objects.filter(room=result.room).count() == 2

    def test_unknown_currency_code_falls_back_to_the_room_currency(self, run_import, db, user, currency):
        parsed = SplitwiseCsvParser().parse(
            build_file_like(
                ["2023-03-06,Ikea,Möbel,10.00,EUR,5.00,-5.00"],
            )
        )
        Currency.objects.filter(code="EUR").delete()
        fallback = Currency.objects.create(name="Pound", sign="£", code="GBP")

        result = run_import(parsed=parsed, user=user, currency=fallback)

        assert ParentTransaction.objects.filter(room=result.room, currency=fallback).count() == 1
