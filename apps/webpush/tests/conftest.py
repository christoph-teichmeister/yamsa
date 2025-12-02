from decimal import Decimal

import pytest

from apps.debt.handlers.events.optimise_debts import calculate_optimised_debts
from apps.transaction.messages.events.transaction import ParentTransactionCreated
from apps.transaction.models import ChildTransaction
from apps.transaction.tests.factories import ParentTransactionFactory


@pytest.fixture
def create_parent_transaction_with_optimisation():
    def _create(
        room,
        paid_by,
        paid_for_tuple,
        parent_transaction_kwargs=None,
        child_transaction_kwargs=None,
    ):
        parent_kwargs = parent_transaction_kwargs or {}
        child_kwargs = child_transaction_kwargs or {}

        parent_transaction = ParentTransactionFactory(
            room=room,
            paid_by=paid_by,
            currency=room.preferred_currency,
            **parent_kwargs,
        )

        children = []
        for paid_for_user in paid_for_tuple:
            child_data = {
                "parent_transaction": parent_transaction,
                "paid_for": paid_for_user,
                "value": Decimal("10"),
                **child_kwargs,
            }
            children.append(ChildTransaction.objects.create(**child_data))

        calculate_optimised_debts(ParentTransactionCreated.Context(parent_transaction=parent_transaction, room=room))

        return parent_transaction, tuple(children)

    return _create
