import pytest

from apps.account.models import UserFriendship
from apps.account.tests.factories import GuestUserFactory, UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.room.models import Room, UserConnectionToRoom
from apps.room.services.suggested_guest_service import SuggestedGuestService


@pytest.mark.django_db
class TestSuggestedGuestService:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.currency = CurrencyFactory()
        self.creator = UserFactory(is_guest=False)
        self.friendliest = UserFactory(is_guest=False)
        self.recurring = UserFactory(is_guest=False)
        self.guest_user = GuestUserFactory()

        self.room_one = Room.objects.create(
            name="Trip One",
            description="Desc",
            preferred_currency=self.currency,
            created_by=self.creator,
        )
        self.room_two = Room.objects.create(
            name="Trip Two",
            description="Desc",
            preferred_currency=self.currency,
            created_by=self.creator,
        )

        UserConnectionToRoom.objects.create(user=self.creator, room=self.room_one)
        UserConnectionToRoom.objects.create(user=self.friendliest, room=self.room_one)
        UserConnectionToRoom.objects.create(user=self.recurring, room=self.room_one)

        UserConnectionToRoom.objects.create(user=self.creator, room=self.room_two)
        UserConnectionToRoom.objects.create(user=self.friendliest, room=self.room_two)
        UserConnectionToRoom.objects.create(user=self.guest_user, room=self.room_two)

        UserFriendship.objects.create(user=self.creator, friend=self.friendliest)

    def test_service_returns_friend_first_and_counts_rooms(self):
        suggestions = SuggestedGuestService(user=self.creator).get_suggested_guests()

        assert len(suggestions) >= 2
        assert suggestions[0].user_id == self.friendliest.id
        assert suggestions[0].is_friend
        assert suggestions[0].rooms_together == 2

        non_friend = next(guest for guest in suggestions if not guest.is_friend)
        assert non_friend.user_id == self.recurring.id
        assert non_friend.rooms_together == 1
        assert all(guest.user_id != self.guest_user.id for guest in suggestions)
