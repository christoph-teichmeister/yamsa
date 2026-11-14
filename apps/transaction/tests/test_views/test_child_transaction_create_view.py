import http
from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.room.models import Room
from apps.transaction.models import ChildTransaction
from apps.transaction.tests.factories import ParentTransactionFactory

pytestmark = pytest.mark.django_db


def test_post_closed_room_is_rejected(authenticated_client: Client, closed_room: Room, user: User) -> None:
    parent_transaction = ParentTransactionFactory(room=closed_room, paid_by=user)

    response = authenticated_client.post(
        reverse("transaction:child-transaction-create", kwargs={"room_slug": closed_room.slug}),
        data={
            "parent_transaction": parent_transaction.id,
            "paid_for": user.id,
            "value": Decimal(5),
        },
    )

    assert response.status_code == http.HTTPStatus.FORBIDDEN
    assert not ChildTransaction.objects.filter(parent_transaction=parent_transaction).exists()


def test_get_serves_the_blank_split_row(authenticated_client: Client, room: Room) -> None:
    response = authenticated_client.get(
        reverse("transaction:child-transaction-create", kwargs={"room_slug": room.slug})
    )

    assert response.status_code == http.HTTPStatus.OK
    assert b"split-row" in response.content


def test_post_is_not_allowed(authenticated_client: Client, room: Room, user: User) -> None:
    response = authenticated_client.post(
        reverse("transaction:child-transaction-create", kwargs={"room_slug": room.slug}),
        data={"paid_for": user.id, "value": Decimal(-5)},
    )

    assert response.status_code == http.HTTPStatus.METHOD_NOT_ALLOWED
