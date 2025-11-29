from decimal import Decimal

from apps.transaction.models import ChildTransaction
from apps.transaction.tests.factories import ParentTransactionFactory


def create_parent_transaction_with_optimisation(
    room,
    paid_by,
    paid_for_tuple,
    parent_transaction_kwargs=None,
    child_transaction_kwargs=None,
):
    parent_transaction_kwargs = parent_transaction_kwargs or {}
    child_transaction_kwargs = child_transaction_kwargs or {}
    created_parent_transaction = ParentTransactionFactory(room=room, paid_by=paid_by, **parent_transaction_kwargs)

    created_child_transactions = []
    for child_transaction_user in paid_for_tuple:
        child_kwargs = {
            "parent_transaction": created_parent_transaction,
            "paid_for": child_transaction_user,
            "value": Decimal("13"),
        }
        child_kwargs.update(child_transaction_kwargs)
        created_child_transactions.append(ChildTransaction.objects.create(**child_kwargs))

    created_child_transactions = tuple(created_child_transactions)

    from apps.debt.handlers.events.optimise_debts import calculate_optimised_debts
    from apps.transaction.messages.events.transaction import ParentTransactionCreated

    calculate_optimised_debts(
        ParentTransactionCreated.Context(
            parent_transaction=created_parent_transaction, room=created_parent_transaction.room
        )
    )

    return created_parent_transaction, created_child_transactions
