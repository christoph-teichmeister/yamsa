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


def test_a_closed_room_renders_the_form_inert(authenticated_client, closed_room):
    """The POST is rejected by the mixin; the page has to say so before anyone types."""
    content = authenticated_client.get(
        reverse("room:userconnectiontoroom-create", kwargs={"room_slug": closed_room.slug})
    ).content.decode()

    assert "This room is closed, so new members cannot be added." in content
    # Both the field and the submit carry the disabled attribute, so nothing invites an attempt.
    assert content.count("disabled") >= 2


def test_an_open_room_renders_a_usable_form(authenticated_client, room):
    content = authenticated_client.get(
        reverse("room:userconnectiontoroom-create", kwargs={"room_slug": room.slug})
    ).content.decode()

    assert "This room is closed, so new members cannot be added." not in content
    assert "Add existing user" in content
