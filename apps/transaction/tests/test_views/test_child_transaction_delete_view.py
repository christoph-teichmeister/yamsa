import http
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.transaction.models import ChildTransaction
from apps.transaction.tests.factories import ChildTransactionFactory, ParentTransactionFactory

pytestmark = pytest.mark.django_db


def test_post_closed_room_is_rejected(authenticated_client, closed_room, user, guest_user):
    parent_transaction = ParentTransactionFactory(room=closed_room, paid_by=user)
    child_transaction = ChildTransactionFactory(
        parent_transaction=parent_transaction,
        paid_for=user,
        value=Decimal("5"),
    )
    ChildTransactionFactory(
        parent_transaction=parent_transaction,
        paid_for=guest_user,
        value=Decimal("5"),
    )

    response = authenticated_client.post(
        reverse(
            "transaction:child-transaction-delete",
            kwargs={"room_slug": closed_room.slug, "pk": child_transaction.pk},
        ),
    )

    assert response.status_code == http.HTTPStatus.FORBIDDEN
    assert ChildTransaction.objects.filter(pk=child_transaction.pk).exists()
