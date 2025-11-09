import http
from datetime import UTC, datetime

from django.urls import reverse
from freezegun import freeze_time

from apps.account.models import User
from apps.account.views import GuestCreateView, UserListForRoomView
from apps.core.tests.setup import BaseTestSetUp
from apps.room.models import UserConnectionToRoom


@freeze_time("2020-04-04 04:20")
class GuestCreateViewTestCase(BaseTestSetUp):
    def test_get_regular(self):
        client = self.reauthenticate_user(self.user)
        response = client.get(reverse("account:guest-create", kwargs={"room_slug": self.room.slug}))
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertTrue(response.template_name[0], GuestCreateView.template_name)
        response_content = response.content.decode()
        self.assertIn(f"Invite a guest to {self.room.name}", response_content)

        self.assertEqual(response.context_data["active_tab"], "people")

    def test_post_regular(self):
        guest_name = "Guest Name"

        client = self.reauthenticate_user(self.user)
        response = client.post(
            reverse("account:guest-create", kwargs={"room_slug": self.room.slug}),
            data={"room_slug": self.room.slug, "name": guest_name},
            follow=True,
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        # Assert that we've been redirected to the roster view
        self.assertTrue(response.template_name[0], UserListForRoomView.template_name)
        response_content = response.content.decode()
        self.assertIn("Room roster", response_content)
        self.assertIn("Add guest", response_content)

        self.assertEqual(response.context_data["active_tab"], "people")

        new_guest = User.objects.get(name=guest_name)
        self.assertTrue(new_guest.is_guest)
        self.assertTrue(new_guest.rooms.filter(id=self.room.id).exists())
        self.assertEqual(new_guest.created_by, self.user)
        self.assertEqual(new_guest.created_at, datetime(2020, 4, 4, 4, 20, tzinfo=UTC))

        self.assertIsNotNone(UserConnectionToRoom.objects.get(user=new_guest, room=self.room))
