from decimal import Decimal
from typing import Union

from apps.core.event_loop.registry import message_registry
from apps.debt.models import Debt
from apps.transaction.messages.events.transaction import (
    ChildTransactionDeleted,
    ParentTransactionCreated,
    ParentTransactionDeleted,
    ParentTransactionUpdated,
)
from apps.transaction.models import ChildTransaction


@message_registry.register_event(event=ParentTransactionCreated)
@message_registry.register_event(event=ParentTransactionUpdated)
@message_registry.register_event(event=ParentTransactionDeleted)
@message_registry.register_event(event=ChildTransactionDeleted)
def calculate_optimised_debts(
    context: Union[
        ParentTransactionCreated.Context
        | ParentTransactionUpdated.Context
        | ChildTransactionDeleted.Context
        | ParentTransactionDeleted.Context
    ],
):
    room_id = context.room.id

    # Delete all unsettled debts of the room
    Debt.objects.filter(room_id=room_id, settled=False).delete()

    # Retrieve all child_transactions in the room and store them in a tuple
    all_child_transactions_of_room_tuple = tuple(
        ChildTransaction.objects.filter(parent_transaction__room_id=room_id)
        .order_by("value", "parent_transaction__currency")
        .values_list("parent_transaction__currency", "paid_for", "parent_transaction__paid_by", "value")
    )

    # Initialize a dictionary to organize debts by currency sign
    currency_debts = {}

    # Group debts by currency sign
    for currency, debtor, creditor, amount in all_child_transactions_of_room_tuple:
        debt_tuple = (debtor, creditor, amount)
        if currency_debts.get(currency) is None:
            currency_debts[currency] = [debt_tuple]
        else:
            currency_debts[currency].append(debt_tuple)

    # Initialize a dictionary to track transactions for each currency
    currency_transactions = {}

    # Iterate through debts grouped by currency and perform debt consolidation
    for currency, debt_list in currency_debts.items():
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
        currency_transactions[currency] = transactions

    # Initialize tuples to keep track of created and touched debt IDs
    created_debt_tuple = ()

    # Iterate through currency transactions and instantiate new debt objects
    for currency, transaction_list in currency_transactions.items():
        for debtor, creditor, transfer_amount in transaction_list:
            if transfer_amount != Decimal(0):
                created_debt_tuple += (
                    Debt(
                        debitor_id=debtor,
                        creditor_id=creditor,
                        room_id=room_id,
                        value=transfer_amount,
                        currency_id=currency,
                    ),
                )

    # Bulk-create new debt objects
    Debt.objects.bulk_create(created_debt_tuple)
