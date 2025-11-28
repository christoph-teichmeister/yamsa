from django.test import TestCase
from django.urls import reverse

from apps.account.tests.baker_recipes import user as user_recipe
from apps.currency.tests.baker_recipes import currency as currency_recipe
from apps.room.models import Room, UserConnectionToRoom


class RoomShareButtonTests(TestCase):
    def setUp(self):
        self.currency = currency_recipe.make()
        self.owner = user_recipe.make(is_guest=False)
        self.room = Room.objects.create(
            name="Trip Space",
            description="Group",
            preferred_currency=self.currency,
            created_by=self.owner,
        )
        UserConnectionToRoom.objects.create(user=self.owner, room=self.room)
        self.client.force_login(self.owner)

    def test_share_button_shows_for_open_rooms_without_guests(self):
        response = self.client.get(reverse("room:dashboard", kwargs={"room_slug": self.room.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "data-copy-share-url", msg_prefix="Share button should render even without guests"
        )

    def test_share_button_hides_when_room_closed(self):
        self.room.status = Room.StatusChoices.CLOSED
        self.room.save()

        response = self.client.get(reverse("room:dashboard", kwargs={"room_slug": self.room.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "data-copy-share-url")
        self.assertContains(response, "bi-dash-circle")

    def test_who_are_you_partial_calls_out_registration_cta(self):
        self.client.logout()
        guest = user_recipe.make(is_guest=True)
        UserConnectionToRoom.objects.create(user=guest, room=self.room)

        response = self.client.get(reverse("room:detail", kwargs={"room_slug": self.room.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Claim your invitation")
        self.assertContains(response, "Create a free account")
