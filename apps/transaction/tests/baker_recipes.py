from model_bakery import seq
from model_bakery.recipe import Recipe, foreign_key

from apps.account.tests.baker_recipes import user
from apps.currency.tests.baker_recipes import currency
from apps.room.tests.baker_recipes import room
from apps.transaction.models import ParentTransaction

parent_transaction = Recipe(
    ParentTransaction,
    description=seq("Description "),
    further_notes=seq("Further Notes"),
    paid_by=foreign_key(user),
    room=foreign_key(room),
    currency=foreign_key(currency),
)
