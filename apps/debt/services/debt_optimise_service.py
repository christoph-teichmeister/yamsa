from collections import defaultdict
from decimal import Decimal

from django.db.models import F, Sum

from apps.currency.models import Currency
from apps.debt.models import Debt
from apps.transaction.models import ChildTransaction


class DebtOptimiseService:
    """Service responsible for refreshing unsettled debts for a room from current transactions."""

    @staticmethod
    def process(room_id):
        """
        Rebuild the unsettled squad of debts for the requested room.

        Steps:
        1. Purge unsettled debts so the recalculation starts from a clean slate.
        2. Aggregated spent and owed values per user+currency via annotated ChildTransactions.
        3. Fold settled debts back into those aggregates so existing settlements are preserved.
        4. Pair debtors with creditors per currency and create fresh Debt records for the residual transfers.
        """
        # Delete all unsettled debts of the room
        Debt.objects.filter(room_id=room_id).filter(settled=False).delete()

        # Keep a reference to already settled debts so we can reapply their values later.
        settled_debts_qs = Debt.objects.filter(room_id=room_id, settled=True)

        # Work with all child transactions within the room to build per-user balances.
        child_transactions_qs = ChildTransaction.objects.filter(parent_transaction__room_id=room_id)

        balances_by_currency = defaultdict(lambda: defaultdict(lambda: Decimal(0)))

        # Users who paid with their own money for others contribute to a positive balance.
        spent_annotations = (
            child_transactions_qs.exclude(paid_for_id=F("parent_transaction__paid_by_id"))
            .values(
                currency_id=F("parent_transaction__currency_id"),
                user_id=F("parent_transaction__paid_by_id"),
            )
            .annotate(total_spent=Sum("value"))
        )
        for entry in spent_annotations:
            currency_id = entry["currency_id"]
            user_id = entry["user_id"]
            balances_by_currency[currency_id][user_id] += entry["total_spent"]

        # Users who were paid for by another party owe money (negative contribution).
        owed_annotations = (
            child_transactions_qs.exclude(parent_transaction__paid_by_id=F("paid_for_id"))
            .values(
                currency_id=F("parent_transaction__currency_id"),
                user_id=F("paid_for_id"),
            )
            .annotate(total_owed=Sum("value"))
        )
        for entry in owed_annotations:
            currency_id = entry["currency_id"]
            user_id = entry["user_id"]
            balances_by_currency[currency_id][user_id] -= entry["total_owed"]

        # Add back settled debitor totals so their negative movement is not lost.
        settled_debitor_annotations = settled_debts_qs.values("currency_id", "debitor_id").annotate(
            total_settled=Sum("value")
        )
        for entry in settled_debitor_annotations:
            balances_by_currency[entry["currency_id"]][entry["debitor_id"]] += entry["total_settled"]

        # Subtract settled creditor totals because they already received the funds.
        settled_creditor_annotations = settled_debts_qs.values("currency_id", "creditor_id").annotate(
            total_settled=Sum("value")
        )
        for entry in settled_creditor_annotations:
            balances_by_currency[entry["currency_id"]][entry["creditor_id"]] -= entry["total_settled"]

        currencies_qs = Currency.objects.all()

        # Iterate through every currency to keep currency-specific debts separate.
        for currency in currencies_qs:
            currency_balances = balances_by_currency.get(currency.id, {})
            # Drop users whose net balance is zero after aggregations.
            balances = {person: balance for person, balance in currency_balances.items() if balance != Decimal(0)}
            if not balances:
                continue

            debtors = []
            creditors = []

            for person, balance in balances.items():
                if balance < 0:
                    debtors.append((person, balance))
                elif balance > 0:
                    creditors.append((person, balance))

            # Sort debtors ascending (most negative first) and creditors descending (largest positive first).
            debtors.sort(key=lambda x: x[1])
            creditors.sort(key=lambda x: x[1], reverse=True)
            transactions_list = []

            while debtors and creditors:
                debtor, debt = debtors.pop(0)
                creditor, credit = creditors.pop(0)

                transfer_amount = min(-debt, credit)
                balances[debtor] += transfer_amount
                debt += transfer_amount

                balances[creditor] -= transfer_amount
                credit -= transfer_amount

                transactions_list.append((debtor, creditor, transfer_amount))

                # If a participant still has a residual balance, put them back into the queue.
                if balances[debtor] != 0:
                    debtors.append((debtor, debt))
                if balances[creditor] != 0:
                    creditors.append((creditor, credit))

            # Bulk-create new Debt rows for every pairwise transfer left after the pairing loop.
            created_debt_tuple = ()
            for debtor, creditor, transfer_amount in transactions_list:
                # Skip zero transfers that can occur from rounding or exact cancellations.
                if transfer_amount != Decimal(0):
                    created_debt_tuple += (
                        Debt(
                            debitor_id=debtor,
                            creditor_id=creditor,
                            room_id=room_id,
                            value=transfer_amount,
                            currency_id=currency.id,
                        ),
                    )

            Debt.objects.bulk_create(created_debt_tuple)
