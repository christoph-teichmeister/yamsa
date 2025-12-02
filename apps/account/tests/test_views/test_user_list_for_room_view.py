import http

import pytest
from django.urls import reverse

from apps.account.views import UserListForRoomView

pytestmark = pytest.mark.django_db


def test_get_for_user_of_room_and_for_superuser_not_of_room(authenticated_client, hx_client, room, superuser, user):
    user_connection = user.userconnectiontoroom_set.get(room=room)
    user_connection.user_has_seen_this_room = True
    user_connection.save()

    superuser_client = hx_client(superuser)

    for client_instance in (authenticated_client, superuser_client):
        response = client_instance.get(reverse("account:list", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        assert response.template_name[0] == UserListForRoomView.template_name

        content = response.content.decode()
        assert "Room roster" in content
        assert user.name in content
        assert "Registered roommate" in content
        assert "Seen room" in content
