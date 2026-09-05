from apps.importer.parsers.splitwise import SplitwiseCsvParser
from apps.importer.tests.factories import DEFAULT_ROWS, build_file_like
from apps.transaction.models import ParentTransaction


class TestImportServiceRepeatedImports:
    def test_second_import_creates_a_separate_room(self, run_import, db, user, currency, parsed):
        first = run_import(parsed=parsed, user=user, currency=currency)
        second_parsed = SplitwiseCsvParser().parse(build_file_like(DEFAULT_ROWS))
        second = run_import(parsed=second_parsed, user=user, currency=currency)

        assert first.room.pk != second.room.pk
        assert ParentTransaction.objects.filter(room=first.room).count() == 2
        assert ParentTransaction.objects.filter(room=second.room).count() == 2

    def test_repeated_import_does_not_touch_the_first_room(self, run_import, db, user, currency, parsed):
        first = run_import(parsed=parsed, user=user, currency=currency)
        before = set(ParentTransaction.objects.filter(room=first.room).values_list("pk", flat=True))

        second_parsed = SplitwiseCsvParser().parse(build_file_like(DEFAULT_ROWS))
        run_import(parsed=second_parsed, user=user, currency=currency)

        after = set(ParentTransaction.objects.filter(room=first.room).values_list("pk", flat=True))
        assert before == after
