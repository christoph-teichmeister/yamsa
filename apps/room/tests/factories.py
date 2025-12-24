import uuid

import factory
from factory import Faker, LazyFunction, SubFactory

from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.room.models import Room, UserConnectionToRoom


class RoomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Room

    slug = LazyFunction(uuid.uuid4)
    share_hash = LazyFunction(Room.generate_share_hash)
    name = Faker("company")
    description = Faker("paragraph")
    created_by = SubFactory(UserFactory)
    preferred_currency = SubFactory(CurrencyFactory)


class UserConnectionToRoomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserConnectionToRoom

    user = SubFactory(UserFactory)
    room = SubFactory(RoomFactory)
