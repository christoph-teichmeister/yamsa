from collections.abc import Callable

from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.account.models import User
from apps.currency.models import Currency
from apps.importer.parsers.splitwise import SplitwiseCsvParser
from apps.importer.tests.factories import build_file_like
from apps.transaction.models import ChildTransaction, ParentTransaction


def _rows(count: int) -> list[str]:
    return [f"2023-02-{(index % 27) + 1:02d},Item {index},Allgemein,10.00,EUR,10.00,-10.00" for index in range(count)]


class TestImportQueryCount:
    """Writing transactions must not cost queries per row: a 2000 row file runs in one request."""

    def _count_queries(self, run_import: Callable, user: User, currency: Currency, rows: int) -> int:
        parsed = SplitwiseCsvParser().parse(build_file_like(_rows(rows)))
        with CaptureQueriesContext(connection) as queries:
            result = run_import(parsed=parsed, user=user, currency=currency)
        assert ParentTransaction.objects.filter(room=result.room).count() == rows
        assert ChildTransaction.objects.filter(parent_transaction__room=result.room).count() == rows
        return len(queries)

    def test_query_count_does_not_grow_with_row_count(
        self, run_import: Callable, db: None, user: User, currency: Currency
    ) -> None:
        small = self._count_queries(run_import, user, currency, rows=5)
        large = self._count_queries(run_import, user, currency, rows=60)

        assert large == small
