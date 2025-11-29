import factory
from factory import Faker, Sequence, SubFactory

from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.room.tests.factories import RoomFactory
from apps.transaction.models import Category, ParentTransaction


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    slug = Sequence(lambda sequence: f"category-{sequence}")
    name = Faker("word")
    emoji = "💰"
    color = "#E0E0E0"
    is_default = False


class ParentTransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ParentTransaction

    description = Faker("sentence", nb_words=6)
    paid_by = SubFactory(UserFactory)
    room = SubFactory(RoomFactory)
    currency = SubFactory(CurrencyFactory)
    category = SubFactory(CategoryFactory)
