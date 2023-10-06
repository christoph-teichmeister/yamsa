from decimal import Decimal

from django.db.models import Q

from apps.core.event_loop.registry import message_registry
from apps.currency.models import Currency
from apps.debt.models import NewDebt, Debt
from apps.transaction.messages.events.transaction import TransactionCreated


@message_registry.register_event(event=TransactionCreated)
def calculate_optimised_debts(context: TransactionCreated.Context):
    all_debts_of_room_tuple = tuple(
        Debt.objects.filter(transaction__room_id=context.transaction.room_id)
        .order_by("transaction__value", "transaction__currency__sign")
        .values_list("transaction__currency__sign", "user", "transaction__paid_by", "transaction__value")
    )

    currency_debts = {}
    for currency_sign, debtor, creditor, amount in all_debts_of_room_tuple:
        debt_tuple = (debtor, creditor, amount)
        if currency_debts.get(currency_sign) is None:
            currency_debts[currency_sign] = [debt_tuple]
        else:
            currency_debts[currency_sign].append(debt_tuple)

    currency_transactions = {}
    for currency_sign, debt_list in currency_debts.items():
        # Create a dictionary to track how much each person owes or is owed
        balances = {}

        # Populate the balances dictionary based on the provided debts
        for debtor, creditor, amount in debt_list:
            balances[debtor] = balances.get(debtor, 0) - amount
            balances[creditor] = balances.get(creditor, 0) + amount

        # Initialize two lists for debtors and creditors
        debtors = []
        creditors = []

        # Separate debtors and creditors, ignoring those with a balance of 0
        for person, balance in balances.items():
            if balance < 0:
                debtors.append((person, balance))
            elif balance > 0:
                creditors.append((person, balance))

        # Sort debtors and creditors based on the owed amounts
        debtors.sort(key=lambda x: x[1])
        creditors.sort(key=lambda x: x[1], reverse=True)

        # Initialize a list to track the transactions
        transactions = []

        # Perform debt consolidation
        while debtors and creditors:
            debtor, debt = debtors[0]
            creditor, credit = creditors[0]

            # Calculate the amount to transfer
            transfer_amount = min(-debt, credit)

            # Update balances and create a transaction
            balances[debtor] += transfer_amount
            balances[creditor] -= transfer_amount

            # Add the transaction to the list
            transactions.append((debtor, creditor, transfer_amount))

            # Remove debtors and creditors with zero balance
            if balances[debtor] == 0:
                debtors.pop(0)
            if balances[creditor] == 0:
                creditors.pop(0)

        currency_transactions[currency_sign] = transactions

    created_debt_ids_tuple = ()
    touched_debt_ids_tuple = ()
    for currency_sign, transaction_list in currency_transactions.items():
        for debtor, creditor, transfer_amount in transaction_list:
            debt_qs = NewDebt.objects.filter(
                room=context.transaction.room,
                debitor=debtor,
                creditor=creditor,
                currency__sign=currency_sign,
                settled=False,
            )

            if not debt_qs.exists():
                if transfer_amount != Decimal(0):
                    created_debt_ids_tuple += (
                        NewDebt.objects.create(
                            debitor_id=debtor,
                            creditor_id=creditor,
                            room=context.transaction.room,
                            value=transfer_amount,
                            currency=Currency.objects.get(sign=currency_sign),
                        ).id,
                    )
                    continue

            if debt_qs.count() == 1:
                debt = debt_qs.first()
                if transfer_amount != Decimal(0):
                    debt.value = transfer_amount
                    debt.save()
                    touched_debt_ids_tuple += (debt.id,)
                else:
                    debt.delete()

        # Delete any untouched, unsettled debt objects
        NewDebt.objects.exclude(Q(id__in=(created_debt_ids_tuple + touched_debt_ids_tuple)) | Q(settled=True)).delete()
