import http

import pytest
from django.urls import reverse

from apps.transaction.views import TransactionListView

pytestmark = pytest.mark.django_db


def test_post_as_anonymous_user(client, room, guest_user):
    response = client.post(
        reverse("account:guest-login"),
        data={"room_slug": room.slug, "user_id": guest_user.id},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == TransactionListView.template_name
    assert "Room transactions" in response.content.decode()


def test_post_as_registered_user(authenticated_client, room, user):
    response = authenticated_client.post(
        reverse("account:guest-login"),
        data={"room_slug": room.slug, "user_id": user.id},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == TransactionListView.template_name
    assert "Room transactions" in response.content.decode()
