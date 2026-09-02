import http
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.transaction.models import ChildTransaction
from apps.transaction.tests.factories import ParentTransactionFactory

pytestmark = pytest.mark.django_db


def test_post_closed_room_is_rejected(authenticated_client, closed_room, user):
    parent_transaction = ParentTransactionFactory(room=closed_room, paid_by=user)

    response = authenticated_client.post(
        reverse("transaction:child-transaction-create", kwargs={"room_slug": closed_room.slug}),
        data={
            "parent_transaction": parent_transaction.id,
            "paid_for": user.id,
            "value": Decimal("5"),
        },
    )

    assert response.status_code == http.HTTPStatus.FORBIDDEN
    assert not ChildTransaction.objects.filter(parent_transaction=parent_transaction).exists()
