import http

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
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
