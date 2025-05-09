from model_bakery import seq
from model_bakery.recipe import Recipe, foreign_key

from apps.account.tests.baker_recipes import user
from apps.room.models import Room

room = Recipe(
    Room,
    name=seq("Vacation "),
    description="A description",
    created_by=foreign_key(user),
)
