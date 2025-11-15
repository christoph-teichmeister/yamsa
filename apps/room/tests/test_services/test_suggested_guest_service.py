from django.test import TestCase

from apps.account.models import UserFriendship
from apps.account.tests.baker_recipes import user as user_recipe
from apps.currency.tests.baker_recipes import currency as currency_recipe
from apps.room.models import Room, UserConnectionToRoom
from apps.room.services.suggested_guest_service import SuggestedGuestService


class SuggestedGuestServiceTest(TestCase):
    def setUp(self):
        self.currency = currency_recipe.make()
        self.creator = user_recipe.make(is_guest=False)
        self.friendliest = user_recipe.make(is_guest=False)
        self.recurring = user_recipe.make(is_guest=False)
        self.guest_user = user_recipe.make(is_guest=True)

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

        self.assertGreaterEqual(len(suggestions), 2)
        self.assertEqual(suggestions[0].user_id, self.friendliest.id)
        self.assertTrue(suggestions[0].is_friend)
        self.assertEqual(suggestions[0].rooms_together, 2)

        non_friend = [guest for guest in suggestions if not guest.is_friend][0]
        self.assertEqual(non_friend.user_id, self.recurring.id)
        self.assertEqual(non_friend.rooms_together, 1)
        self.assertFalse(any(guest.user_id == self.guest_user.id for guest in suggestions))
