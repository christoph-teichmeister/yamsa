from decimal import Decimal

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
    context: ParentTransactionCreated.Context
    | ParentTransactionUpdated.Context
    | ChildTransactionDeleted.Context
    | ParentTransactionDeleted.Context,
):
    room_id = context.room.id

    base_debt_qs = Debt.objects.filter(room_id=room_id)

    # Delete all unsettled debts of the room
    base_debt_qs.filter(settled=False).delete()

    # Retrieve all child_transactions in the room and store them in a tuple
    all_child_transactions_of_room_tuple = tuple(
        ChildTransaction.objects.filter(parent_transaction__room_id=room_id)
        .order_by("value", "parent_transaction__currency")
        .values_list("parent_transaction__currency", "paid_for", "parent_transaction__paid_by", "value")
    )

    # Retrieve all settled debts of the room and store them in a tuple
    settled_debts_values_list = base_debt_qs.filter(settled=True).values_list(
        "currency", "debitor", "creditor", "value"
    )

    # child_transactions will include transactions made from person A to themselves - exclude those here
    excluded_child_transactions = tuple(filter(lambda ct: ct[1] != ct[2], all_child_transactions_of_room_tuple))

    # Iterate over settled debts
    for settled_debt in settled_debts_values_list:
        currency, debitor, creditor, settled_value = settled_debt

        # Find corresponding child transactions of the debt debitor
        debitor_child_transactions = tuple(
            filter(
                lambda ct: ct[0] == currency and ct[1] == debitor,
                excluded_child_transactions,
            )
        )

        # Reduce the value of child transactions by settled debt value
        for transaction in debitor_child_transactions:
            transaction_currency, paid_for, paid_by, value = transaction
            if value >= settled_value:
                # If the transaction value is greater than or equal to the settled debt value,
                # reduce the transaction value by the settled debt value
                value -= settled_value
                settled_value = 0
            else:
                # If the transaction value is less than the settled debt value,
                # reduce the settled debt value by the transaction value
                settled_value -= value
                value = 0

            # Update the value of the transaction
            all_child_transactions_of_room_tuple = tuple(
                (t[0], t[1], t[2], value if (t[0] == transaction_currency and t[1] == paid_for) else t[3])
                for t in all_child_transactions_of_room_tuple
            )

            # If settled debt value becomes 0, break the loop
            if settled_value == 0:
                break

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
            transactions.append((debtor, creditor, transfer_amount))

            # Remove debtors and creditors with zero balance
            if balances[debtor] != 0:
                debtors.append((debtor, debt))
            if balances[creditor] != 0:
                creditors.append((creditor, credit))

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
