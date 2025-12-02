import http

import pytest
from django.urls import reverse

from apps.room.models import UserConnectionToRoom


@pytest.mark.django_db
class TestRoomToRequestMiddleware:
    def test_middleware_sets_user_has_seen_this_room_properly(self, authenticated_client, user, room):
        connection = UserConnectionToRoom.objects.get(user=user, room=room)
        assert not connection.user_has_seen_this_room

        response = authenticated_client.get(reverse("room:detail", kwargs={"room_slug": room.slug}))
        assert response.status_code == http.HTTPStatus.OK

        connection.refresh_from_db()
        assert connection.user_has_seen_this_room

    def test_middleware_allows_superuser_to_see_a_room(self, client, superuser, room):
        client.defaults["HTTP_HX_REQUEST"] = "true"
        client.force_login(superuser)

        response = client.get(reverse("room:detail", kwargs={"room_slug": room.slug}))
        assert response.status_code == http.HTTPStatus.OK
