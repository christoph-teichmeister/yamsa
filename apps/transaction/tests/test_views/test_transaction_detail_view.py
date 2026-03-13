import http

import pytest
from django.urls import reverse

from apps.transaction.tests.factories import ParentTransactionFactory

pytestmark = pytest.mark.django_db


def test_transaction_detail_shows_receipt_empty_state(client, room, user):
    parent_transaction = ParentTransactionFactory(room=room, paid_by=user, currency=room.preferred_currency)
    client.force_login(user)

    response = client.get(reverse("transaction:detail", kwargs={"room_slug": room.slug, "pk": parent_transaction.pk}))

    assert response.status_code == http.HTTPStatus.OK
    content = response.content.decode()
    assert "No receipts have been attached to this transaction yet." in content
