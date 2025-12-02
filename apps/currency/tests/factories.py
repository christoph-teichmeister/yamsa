import factory
from factory import Sequence

from apps.currency.models import Currency


class CurrencyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Currency

    name = Sequence(lambda sequence: f"Currency {sequence}")
    sign = "₿"
    code = Sequence(lambda sequence: f"C{sequence:04d}")
