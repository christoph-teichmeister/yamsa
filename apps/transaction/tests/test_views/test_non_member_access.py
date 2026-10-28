import http

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.tests.factories import UserFactory
from apps.room.models import Room

pytestmark = pytest.mark.django_db


ROOM_SCOPED_URLS = (
    ("transaction:create", {}),
    ("transaction:list", {}),
    ("transaction:export", {}),
    ("transaction:feed", {}),
    ("transaction:detail", {"pk": 1}),
    ("transaction:receipt-upload", {"transaction_pk": 1}),
    ("transaction:receipt-delete", {"receipt_pk": 1}),
    ("transaction:category-breakdown", {}),
    ("transaction:category-manager", {}),
    ("transaction:edit", {"pk": 1}),
    ("transaction:child-transaction-create", {}),
    ("transaction:child-transaction-delete", {"pk": 1}),
    ("transaction:parent-transaction-delete", {"pk": 1}),
    ("debt:list", {}),
    ("debt:export", {}),
    ("debt:settle", {"pk": 1}),
    ("debt:money-spent-on-room", {}),
    ("debt:money-spent-trend", {}),
)


class TestNonMemberAccess:
    @pytest.mark.parametrize(("url_name", "extra_kwargs"), ROOM_SCOPED_URLS)
    @pytest.mark.parametrize("method", ["get", "post"])
    def test_a_user_outside_the_room_is_refused(
        self, client: Client, room: Room, url_name: str, extra_kwargs: dict, method: str
    ) -> None:
        client.force_login(UserFactory())

        response = getattr(client, method)(reverse(url_name, kwargs={"room_slug": room.slug, **extra_kwargs}))

        assert response.status_code == http.HTTPStatus.FORBIDDEN
