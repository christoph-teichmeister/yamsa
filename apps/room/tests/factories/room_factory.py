import uuid

import factory
from factory import Faker, LazyFunction, SubFactory

from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.room.models import Room


class RoomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Room

    slug = LazyFunction(uuid.uuid4)
    share_hash = LazyFunction(Room.generate_share_hash)
    name = Faker("company")
    # Room.description is a TextField(max_length=50), which only the forms enforce — a longer
    # fixture is data the app itself would reject, and every test editing such a room fails
    # on a field it never touched.
    description = Faker("sentence", nb_words=4)
    created_by = SubFactory(UserFactory)
    preferred_currency = SubFactory(CurrencyFactory)
