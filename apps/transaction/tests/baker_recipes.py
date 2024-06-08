from decimal import Decimal

from model_bakery import baker, seq
from model_bakery.recipe import Recipe, foreign_key

from apps.account.tests.baker_recipes import user
from apps.currency.tests.baker_recipes import currency
from apps.room.tests.baker_recipes import room
from apps.transaction.models import ChildTransaction, ParentTransaction

parent_transaction = Recipe(
    ParentTransaction,
    description=seq("Description "),
    further_notes=seq("Further Notes"),
    paid_by=foreign_key(user),
    room=foreign_key(room),
    currency=foreign_key(currency),
    created_by=foreign_key(user),
)

child_transaction = Recipe(
    ChildTransaction,
    parent_transaction=foreign_key(parent_transaction),
    paid_for=foreign_key(user),
    value=Decimal(13),
)


def create_parent_transaction_with_optimisation(
    room, paid_by, paid_for_tuple, parent_transaction_kwargs={}, child_transaction_kwargs={}
):
    created_parent_transaction = baker.make_recipe(
        "apps.transaction.tests.parent_transaction", room=room, paid_by=paid_by, **parent_transaction_kwargs
    )

    created_child_transactions = ()
    for child_transaction_user in paid_for_tuple:
        created_child_transactions += (
            baker.make_recipe(
                "apps.transaction.tests.child_transaction",
                parent_transaction=created_parent_transaction,
                paid_for=child_transaction_user,
                **child_transaction_kwargs,
            ),
        )

    from apps.debt.handlers.events.optimise_debts import calculate_optimised_debts
    from apps.transaction.messages.events.transaction import ParentTransactionCreated

    calculate_optimised_debts(
        ParentTransactionCreated.Context(
            parent_transaction=created_parent_transaction, room=created_parent_transaction.room
        )
    )

    return created_parent_transaction, created_child_transactions
