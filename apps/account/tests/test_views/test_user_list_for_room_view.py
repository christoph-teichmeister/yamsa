import http

import pytest
from django.urls import reverse

from apps.account.models import User
from apps.account.views import UserListForRoomView
from apps.room.tests.factories import RoomFactory, UserConnectionToRoomFactory

pytestmark = pytest.mark.django_db


def test_get_for_user_of_room_and_for_superuser_not_of_room(
    authenticated_client,
    room,
    user,
    superuser_htmx_client,
):
    user_connection = user.userconnectiontoroom_set.get(room=room)
    user_connection.user_has_seen_this_room = True
    user_connection.save()

    expectations = (
        (authenticated_client, True),
        (superuser_htmx_client, False),
    )

    for client_instance, should_show_room_roster in expectations:
        response = client_instance.get(reverse("account:list", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        assert response.template_name[0] == UserListForRoomView.template_name

        content = response.content.decode()
        if should_show_room_roster:
            assert "Room roster" in content
            assert user.name in content
            assert "Registered roommate" in content
            assert "Seen room" in content
        else:
            assert "Guest access" in content


def test_user_has_seen_annotation_scopes_to_requested_room(user):
    room_one = RoomFactory(created_by=user)
    room_two = RoomFactory(created_by=user)

    UserConnectionToRoomFactory(user=user, room=room_one, user_has_seen_this_room=True)
    UserConnectionToRoomFactory(user=user, room=room_two, user_has_seen_this_room=False)

    for current_room, expected_flag in ((room_one, True), (room_two, False)):
        queryset = User.objects.get_for_room_slug(room_slug=current_room.slug).annotate_user_has_seen_this_room(
            room_id=current_room.id
        )

        assert queryset.get(id=user.id).user_has_seen_this_room is expected_flag
