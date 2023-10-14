from decimal import Decimal

from django.db.models import Q

from apps.core.event_loop.registry import message_registry
from apps.currency.models import Currency
from apps.debt.models import Debt
from apps.transaction.messages.events.transaction import TransactionCreated


@message_registry.register_event(event=TransactionCreated)
def calculate_optimised_debts(context: TransactionCreated.Context):
    # Retrieve all unsettled debts in the room and store them in a tuple
    all_debts_of_room_tuple = tuple(
        Debt.objects.filter(room_id=context.transaction.room_id, settled=False)
        .order_by("value", "currency__sign")
        .values_list("currency__sign", "debitor", "creditor", "value")
    )

    # Initialize a dictionary to organize debts by currency sign
    currency_debts = {}

    # Group debts by currency sign
    for currency_sign, debtor, creditor, amount in all_debts_of_room_tuple:
        debt_tuple = (debtor, creditor, amount)
        if currency_debts.get(currency_sign) is None:
            currency_debts[currency_sign] = [debt_tuple]
        else:
            currency_debts[currency_sign].append(debt_tuple)

    # Insert data of created transaction into currency_debts
    for debtor in context.transaction.paid_for.all():
        debt_tuple = (debtor.id, context.transaction.paid_by.id, context.transaction.value)
        currency_sign = context.transaction.currency.sign

        if currency_debts.get(currency_sign) is None:
            currency_debts[currency_sign] = [debt_tuple]
        else:
            currency_debts[currency_sign].append(debt_tuple)

    # Initialize a dictionary to track transactions for each currency
    currency_transactions = {}

    # Iterate through debts grouped by currency and perform debt consolidation
    for currency_sign, debt_list in currency_debts.items():
        # Initialize a dictionary to track how much each person owes or is owed
        balances = {}

        # Populate the balances dictionary based on the provided debts
        for debtor, creditor, amount in debt_list:
            balances[debtor] = balances.get(debtor, 0) - amount
            balances[creditor] = balances.get(creditor, 0) + amount

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

        # Store the resulting transactions in the dictionary
        currency_transactions[currency_sign] = transactions

    # Initialize tuples to keep track of created and touched debt IDs
    created_debt_ids_tuple = ()
    touched_debt_ids_tuple = ()

    # Iterate through currency transactions and update or create debt objects
    for currency_sign, transaction_list in currency_transactions.items():
        for debtor, creditor, transfer_amount in transaction_list:
            # Query existing debt objects for the current transaction
            debt_qs = Debt.objects.filter(
                room_id=context.transaction.room_id,
                debitor=debtor,
                creditor=creditor,
                currency__sign=currency_sign,
                settled=False,
            )

            if not debt_qs.exists():
                # Create a new debt object if it doesn't exist
                if transfer_amount != Decimal(0):
                    created_debt_ids_tuple += (
                        Debt.objects.create(
                            debitor_id=debtor,
                            creditor_id=creditor,
                            room_id=context.transaction.room_id,
                            value=transfer_amount,
                            currency=Currency.objects.get(sign=currency_sign),
                        ).id,
                    )
                continue

            if debt_qs.count() == 1:
                # Update or delete an existing debt object based on the transaction
                debt = debt_qs.first()
                if transfer_amount != Decimal(0):
                    debt.value = transfer_amount
                    debt.save()
                    touched_debt_ids_tuple += (debt.id,)
                else:
                    debt.delete()

    # Delete any unsettled debt objects that were not touched
    Debt.objects.exclude(Q(id__in=(created_debt_ids_tuple + touched_debt_ids_tuple)) | Q(settled=True)).filter(
        room_id=context.transaction.room_id
    ).delete()
