from django.test import TestCase
from django.urls import reverse

from apps.account.models import UserFriendship
from apps.account.tests.baker_recipes import user as user_recipe
from apps.currency.tests.baker_recipes import currency as currency_recipe
from apps.room.models import Room, UserConnectionToRoom


class SuggestedGuestViewsTest(TestCase):
    def setUp(self):
        self.currency = currency_recipe.make()
        self.creator = user_recipe.make(is_guest=False)
        self.collaborator = user_recipe.make(is_guest=False)
        self.room = Room.objects.create(
            name="Group Trip",
            description="Desc",
            preferred_currency=self.currency,
            created_by=self.creator,
        )
        UserConnectionToRoom.objects.create(user=self.creator, room=self.room)
        UserConnectionToRoom.objects.create(user=self.collaborator, room=self.room)

        self.client.force_login(self.creator)

    def test_room_create_view_injects_suggestions(self):
        response = self.client.get(reverse("room:create"))
        self.assertEqual(response.status_code, 200)
        suggestions = response.context.get("suggested_guests", [])
        self.assertTrue(any(guest.user_id == self.collaborator.id for guest in suggestions))

    def test_friend_toggle_view_flips_state(self):
        url = reverse("room:htmx-suggested-guest-friend-toggle")
        response = self.client.post(url, {"suggested_user_id": self.collaborator.id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserFriendship.objects.filter(user=self.creator, friend=self.collaborator).exists())
        self.assertIn("Friend", response.content.decode())

        response = self.client.post(url, {"suggested_user_id": self.collaborator.id})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(UserFriendship.objects.filter(user=self.creator, friend=self.collaborator).exists())

    def test_existing_room_view_includes_suggestions(self):
        url = reverse("room:userconnectiontoroom-create", kwargs={"room_slug": self.room.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        suggestions = response.context.get("suggested_guests", [])
        self.assertTrue(any(guest.user_id == self.collaborator.id for guest in suggestions))
