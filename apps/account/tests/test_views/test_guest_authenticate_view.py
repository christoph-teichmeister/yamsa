import http

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.account.tests.factories import GuestUserFactory
from apps.room.models import Room
from apps.transaction.views import TransactionListView

pytestmark = pytest.mark.django_db


def test_post_as_anonymous_user(client: Client, room: Room, guest_user: User) -> None:
    response = client.post(
        reverse("account:guest-login"),
        data={"room_slug": room.slug, "user_id": guest_user.id},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == TransactionListView.template_name
    assert "Room transactions" in response.content.decode()


def test_post_as_registered_user(authenticated_client: Client, room: Room, user: User) -> None:
    response = authenticated_client.post(
        reverse("account:guest-login"),
        data={"room_slug": room.slug, "user_id": user.id},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == TransactionListView.template_name
    assert "Room transactions" in response.content.decode()


def test_post_registered_user_id_is_rejected(client: Client, room: Room, user: User) -> None:
    response = client.post(reverse("account:guest-login"), data={"room_slug": room.slug, "user_id": user.id})

    assert response.status_code == http.HTTPStatus.NOT_FOUND
    assert "_auth_user_id" not in client.session


def test_post_guest_of_another_room_is_rejected(client: Client, room: Room) -> None:
    outsider = GuestUserFactory()

    response = client.post(reverse("account:guest-login"), data={"room_slug": room.slug, "user_id": outsider.id})

    assert response.status_code == http.HTTPStatus.NOT_FOUND
    assert "_auth_user_id" not in client.session


@pytest.mark.parametrize("user_id", ["999999", "abc", ""])
def test_post_unknown_user_id_is_404(client: Client, room: Room, user_id: str) -> None:
    response = client.post(reverse("account:guest-login"), data={"room_slug": room.slug, "user_id": user_id})

    assert response.status_code == http.HTTPStatus.NOT_FOUND


def test_post_unknown_room_is_404(client: Client, guest_user: User) -> None:
    response = client.post(reverse("account:guest-login"), data={"room_slug": "nope", "user_id": guest_user.id})

    assert response.status_code == http.HTTPStatus.NOT_FOUND
