from itertools import cycle

from model_bakery import seq
from model_bakery.recipe import Recipe

from apps.currency.models import Currency

some_currency_signs = ("€", "$", "£", "¥")

currency = Recipe(
    Currency,
    name=seq("Currency Name "),
    sign=cycle(some_currency_signs),
)
