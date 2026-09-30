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


def test_post_closed_room_is_rejected(authenticated_client: Client, closed_room: Room, user: User):
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
