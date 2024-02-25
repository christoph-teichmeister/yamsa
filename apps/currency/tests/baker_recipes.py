from model_bakery import seq
from model_bakery.recipe import Recipe

from apps.currency.models import Currency

currency = Recipe(
    Currency,
    name=seq("Currency Name "),
    sign=seq("Sign "),
)
