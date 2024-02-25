import http

from django.urls import reverse

from apps.account.views import UserListForRoomView
from apps.core.tests.setup import BaseTestSetUp


class UserListForRoomViewTestCase(BaseTestSetUp):
    def test_get_for_user_of_room_and_for_superuser_not_of_room(self):
        user_connection_to_room = self.user.userconnectiontoroom_set.get(room=self.room)
        user_connection_to_room.user_has_seen_this_room = True
        user_connection_to_room.save()

        for authenticated_user in [self.user, self.superuser]:
            client = self.reauthenticate_user(authenticated_user)
            response = client.get(reverse("account:list", kwargs={"room_slug": self.room.slug}))

            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertTrue(response.template_name[0], UserListForRoomView.template_name)

            stringed_content = str(response.content)
            self.assertIn("People", stringed_content)

            self.assertIn(self.user.name, stringed_content)
            self.assertNotIn(self.user.username, stringed_content)

            self.assertIn("Is a registered user", stringed_content)
            self.assertIn("Has seen this room!", stringed_content)
