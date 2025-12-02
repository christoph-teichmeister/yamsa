import factory
from factory import Faker, Sequence, SubFactory
from faker import Faker as FakerGenerator

from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.room.tests.factories import RoomFactory
from apps.transaction.models import Category, ParentTransaction

fake_generator = FakerGenerator()


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

    description = factory.LazyFunction(lambda: fake_generator.sentence(nb_words=6)[:50])
    paid_by = SubFactory(UserFactory)
    room = SubFactory(RoomFactory)
    currency = SubFactory(CurrencyFactory)
    category = SubFactory(CategoryFactory)
