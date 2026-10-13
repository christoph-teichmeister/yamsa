from collections import defaultdict, deque
from collections.abc import Iterable
from decimal import Decimal

from django.db.models import F, Sum

from apps.currency.models import Currency
from apps.debt.models import Debt
from apps.transaction.models import ChildTransaction


class DebtOptimiseService:
    """Service responsible for refreshing unsettled debts for a room from current transactions."""

    @staticmethod
    def process(room_id: int) -> None:
        """Rebuild the unsettled squad of debts for the requested room.

        Steps:
        1. Purge unsettled debts so the recalculation starts from a clean slate.
        2. Aggregated spent and owed values per user+currency via annotated ChildTransactions.
        3. Fold settled debts back into those aggregates so existing settlements are preserved.
        4. Pair debtors with creditors per currency and create fresh Debt records for the residual transfers.
        """
        Debt.objects.filter(room_id=room_id).filter(settled=False).delete()

        balances_by_currency = DebtOptimiseService._balances_by_currency(room_id)

        Debt.objects.bulk_create(
            Debt(
                debitor_id=debtor,
                creditor_id=creditor,
                room_id=room_id,
                value=transfer_amount,
                currency_id=currency.id,
            )
            for currency in Currency.objects.filter(id__in=balances_by_currency.keys())
            for debtor, creditor, transfer_amount in DebtOptimiseService._transfers(balances_by_currency[currency.id])
        )

    @staticmethod
    def _balances_by_currency(room_id: int) -> dict[int, dict[int, Decimal]]:
        """Net balance per currency and user: positive means the user is owed money."""
        balances_by_currency = defaultdict(lambda: defaultdict(lambda: Decimal(0)))

        def apply(rows: Iterable[dict], user_key: str, sign: int) -> None:
            for row in rows:
                balances_by_currency[row["currency_id"]][row[user_key]] += sign * row["total"]

        child_transactions_qs = ChildTransaction.objects.filter(parent_transaction__room_id=room_id)
        apply(
            child_transactions_qs.exclude(paid_for_id=F("parent_transaction__paid_by_id"))
            .values(currency_id=F("parent_transaction__currency_id"), user_id=F("parent_transaction__paid_by_id"))
            .annotate(total=Sum("value")),
            "user_id",
            1,
        )
        apply(
            child_transactions_qs.exclude(parent_transaction__paid_by_id=F("paid_for_id"))
            .values(currency_id=F("parent_transaction__currency_id"), user_id=F("paid_for_id"))
            .annotate(total=Sum("value")),
            "user_id",
            -1,
        )

        # Settled debts already moved money, so they offset the transaction-based balances.
        settled_debts_qs = Debt.objects.filter(room_id=room_id, settled=True)
        apply(settled_debts_qs.values("currency_id", "debitor_id").annotate(total=Sum("value")), "debitor_id", 1)
        apply(settled_debts_qs.values("currency_id", "creditor_id").annotate(total=Sum("value")), "creditor_id", -1)

        return balances_by_currency

    @staticmethod
    def _transfers(currency_balances: dict[int, Decimal]) -> list[tuple[int, int, Decimal]]:
        """Greedily pair the largest debtors with the largest creditors into (debtor, creditor, amount) transfers."""
        balances = {person: balance for person, balance in currency_balances.items() if balance != Decimal(0)}
        debtors_queue = deque(sorted(((p, b) for p, b in balances.items() if b < 0), key=lambda x: x[1]))
        creditors_queue = deque(
            sorted(((p, b) for p, b in balances.items() if b > 0), key=lambda x: x[1], reverse=True)
        )

        transfers = []
        while debtors_queue and creditors_queue:
            debtor, debt = debtors_queue.popleft()
            creditor, credit = creditors_queue.popleft()

            transfer_amount = min(-debt, credit)
            debt += transfer_amount
            credit -= transfer_amount
            # Zero transfers can occur from rounding or exact cancellations.
            if transfer_amount != Decimal(0):
                transfers.append((debtor, creditor, transfer_amount))

            if debt != 0:
                debtors_queue.append((debtor, debt))
            if credit != 0:
                creditors_queue.append((creditor, credit))

        return transfers
