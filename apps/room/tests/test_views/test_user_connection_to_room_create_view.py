import http

import pytest
from django.urls import reverse

from apps.account.tests.factories import UserFactory
from apps.room.models import UserConnectionToRoom

pytestmark = pytest.mark.django_db


def test_post_regular(authenticated_client, room):
    other_user = UserFactory()

    response = authenticated_client.post(
        reverse("room:userconnectiontoroom-create", kwargs={"room_slug": room.slug}),
        data={"email": other_user.email, "room_slug": room.slug},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert UserConnectionToRoom.objects.filter(user=other_user, room=room).exists()


def test_post_closed_room_is_rejected(authenticated_client, closed_room):
    other_user = UserFactory()

    response = authenticated_client.post(
        reverse("room:userconnectiontoroom-create", kwargs={"room_slug": closed_room.slug}),
        data={"email": other_user.email, "room_slug": closed_room.slug},
    )

    assert response.status_code == http.HTTPStatus.FORBIDDEN
    assert not UserConnectionToRoom.objects.filter(user=other_user, room=closed_room).exists()
