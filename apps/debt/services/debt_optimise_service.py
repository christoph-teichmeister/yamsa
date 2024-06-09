from decimal import Decimal

from django.db.models import Sum

from apps.account.models import User
from apps.currency.models import Currency
from apps.debt.models import Debt
from apps.transaction.models import ChildTransaction


class DebtOptimiseService:
    @staticmethod
    def process(room_id):
        # Delete all unsettled debts of the room
        Debt.objects.filter(room_id=room_id).filter(settled=False).delete()

        settled_debts_qs = Debt.objects.filter(room_id=room_id, settled=True).values(
            "debitor_id", "value", "currency_id"
        )

        currencies_qs = Currency.objects.all()
        users_of_room_qs = User.objects.filter(rooms=room_id)

        for currency in currencies_qs:
            balances = {}
            for user in users_of_room_qs:
                total_spent = ChildTransaction.objects.filter(
                    parent_transaction__room_id=room_id,
                    parent_transaction__currency_id=currency.id,
                    parent_transaction__paid_by_id=user.id,
                ).exclude(paid_for_id=user.id).aggregate(total_spent=Sum("value"))["total_spent"] or Decimal(0)
                balances[user.id] = total_spent

                total_owed = ChildTransaction.objects.filter(
                    parent_transaction__room_id=room_id,
                    parent_transaction__currency_id=currency.id,
                    paid_for_id=user.id,
                ).exclude(parent_transaction__paid_by_id=user.id).aggregate(total_owed=Sum("value"))[
                    "total_owed"
                ] or Decimal(0)
                balances[user.id] -= total_owed

                total_where_they_owed_something = settled_debts_qs.filter(
                    debitor_id=user.id, currency_id=currency.id
                ).aggregate(total_owed_settled=Sum("value"))["total_owed_settled"] or Decimal(0)
                balances[user.id] += total_where_they_owed_something

                total_where_they_credited_something = settled_debts_qs.filter(
                    creditor_id=user.id, currency_id=currency.id
                ).aggregate(total_credited_settled=Sum("value"))["total_credited_settled"] or Decimal(0)
                balances[user.id] -= total_where_they_credited_something

            # Initialize lists for debtors and creditors, ignoring those with a balance of 0
            debtors = []
            creditors = []

            # Separate debtors and creditors and sort them based on the owed amounts
            for person, balance in balances.items():
                if balance < 0:
                    debtors.append((person, balance))
                elif balance > 0:
                    creditors.append((person, balance))

            # Sort debtors and creditors and track transactions
            debtors.sort(key=lambda x: x[1])
            creditors.sort(key=lambda x: x[1], reverse=True)
            transactions_list = []

            # Perform debt consolidation
            while debtors and creditors:
                debtor, debt = debtors.pop(0)
                creditor, credit = creditors.pop(0)

                # Calculate the amount to transfer
                transfer_amount = min(-debt, credit)

                # Update balances and create a transaction
                balances[debtor] += transfer_amount
                debt += transfer_amount

                balances[creditor] -= transfer_amount
                credit -= transfer_amount

                # Add the transaction to the list
                transactions_list.append((debtor, creditor, transfer_amount))

                # Remove debtors and creditors with zero balance
                if balances[debtor] != 0:
                    debtors.append((debtor, debt))
                if balances[creditor] != 0:
                    creditors.append((creditor, credit))

            created_debt_tuple = ()
            for debtor, creditor, transfer_amount in transactions_list:
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

            # Bulk-create new debt objects
            Debt.objects.bulk_create(created_debt_tuple)
