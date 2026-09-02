import http

import pytest
from django.urls import reverse

from apps.transaction.models import ParentTransaction
from apps.transaction.tests.factories import ParentTransactionFactory

pytestmark = pytest.mark.django_db


def test_post_closed_room_is_rejected(authenticated_client, closed_room, user):
    parent_transaction = ParentTransactionFactory(room=closed_room, paid_by=user)

    response = authenticated_client.post(
        reverse(
            "transaction:parent-transaction-delete",
            kwargs={"room_slug": closed_room.slug, "pk": parent_transaction.pk},
        ),
    )

    assert response.status_code == http.HTTPStatus.FORBIDDEN
    assert ParentTransaction.objects.filter(pk=parent_transaction.pk).exists()
