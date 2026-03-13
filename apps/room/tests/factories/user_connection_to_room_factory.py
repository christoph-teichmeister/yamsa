import factory
from factory import SubFactory

from apps.account.tests.factories import UserFactory
from apps.room.models import UserConnectionToRoom
from apps.room.tests.factories.room_factory import RoomFactory


class UserConnectionToRoomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserConnectionToRoom

    user = SubFactory(UserFactory)
    room = SubFactory(RoomFactory)
