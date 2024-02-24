import http

from django.urls import reverse
from model_bakery import baker

from apps.core.tests.setup import BaseTestSetUp
from apps.room.models import UserConnectionToRoom


class RoomToRequestMiddlewareTestCase(BaseTestSetUp):
    def test_middleware_sets_user_has_seen_this_room_properly(self):
        user = baker.make_recipe("apps.account.tests.user")
        room = baker.make_recipe("apps.room.tests.room")
        room.users.add(user)

        self.assertFalse(UserConnectionToRoom.objects.get(user=user, room=room).user_has_seen_this_room)

        client = self.reauthenticate_user(user)
        response = client.get(reverse("room:detail", kwargs={"room_slug": room.slug}))
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertTrue(UserConnectionToRoom.objects.get(user=user, room=room).user_has_seen_this_room)

    def test_middleware_allows_superuser_to_see_a_room(self):
        room = baker.make_recipe("apps.room.tests.room")

        client = self.reauthenticate_user(self.superuser)
        response = client.get(reverse("room:detail", kwargs={"room_slug": room.slug}))
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
