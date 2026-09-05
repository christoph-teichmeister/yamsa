from decimal import Decimal

from apps.news.models import News
from apps.transaction.models import ChildTransaction, ParentTransaction


class TestImportServiceCreatesTransactions:
    def test_every_importable_row_becomes_a_transaction(self, run_import, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        assert ParentTransaction.objects.filter(room=result.room).count() == 2
        assert result.skipped_count == 1

    def test_zero_share_creates_no_child_transaction(self, run_import, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        cambio = ParentTransaction.objects.get(room=result.room, description="Cambio")
        assert cambio.child_transactions.count() == 1
        assert cambio.value == Decimal("25.20")

    def test_transactions_are_attributed_to_the_importer(self, run_import, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        assert all(transaction.created_by == user for transaction in ParentTransaction.objects.filter(room=result.room))
        assert all(
            child.created_by == user for child in ChildTransaction.objects.filter(parent_transaction__room=result.room)
        )

    def test_paid_at_is_timezone_aware(self, run_import, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        transaction = ParentTransaction.objects.filter(room=result.room).first()
        assert transaction.paid_at.tzinfo is not None

    def test_import_writes_a_single_summary_news_entry(self, run_import, db, user, currency, parsed):
        result = run_import(parsed=parsed, user=user, currency=currency)

        import_news = News.objects.filter(room=result.room, message__contains="imported")
        assert import_news.count() == 1
