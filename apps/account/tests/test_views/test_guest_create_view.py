import http
from datetime import UTC, datetime

import pytest
from django.urls import reverse
from freezegun import freeze_time

from apps.account.models import User
from apps.account.views import GuestCreateView, UserListForRoomView
from apps.room.models import UserConnectionToRoom

pytestmark = pytest.mark.django_db


@freeze_time("2020-04-04 04:20")
def test_get_regular(authenticated_client, room):
    response = authenticated_client.get(reverse("account:guest-create", kwargs={"room_slug": room.slug}))

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == GuestCreateView.template_name
    content = response.content.decode()
    assert f'Invite a guest to "{room.name}"' in content
    assert response.context_data["active_tab"] == "people"


@freeze_time("2020-04-04 04:20")
def test_post_regular(authenticated_client, room, user):
    guest_name = "Guest Name"

    response = authenticated_client.post(
        reverse("account:guest-create", kwargs={"room_slug": room.slug}),
        data={"room_slug": room.slug, "name": guest_name},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == UserListForRoomView.template_name
    content = response.content.decode()
    assert "Room roster" in content
    assert "Add guest" in content
    assert response.context_data["active_tab"] == "people"

    new_guest = User.objects.get(name=guest_name)
    assert new_guest.is_guest
    assert new_guest.rooms.filter(id=room.id).exists()
    assert new_guest.created_by == user
    assert new_guest.created_at == datetime(2020, 4, 4, 4, 20, tzinfo=UTC)
    assert UserConnectionToRoom.objects.filter(user=new_guest, room=room).exists()
