import http

import pytest
from django.urls import reverse

from apps.debt.models import Debt
from apps.transaction.models import ParentTransaction
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation
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


def test_deleting_a_transaction_clears_the_debt_it_caused(authenticated_client, room, user, guest_user):
    parent_transaction, _ = create_parent_transaction_with_optimisation(
        room=room, paid_by=user, paid_for_tuple=(user, guest_user)
    )
    assert Debt.objects.filter(room=room, settled=False, debitor=guest_user).exists()

    response = authenticated_client.post(
        reverse(
            "transaction:parent-transaction-delete",
            kwargs={"room_slug": room.slug, "pk": parent_transaction.pk},
        ),
    )

    assert response.status_code == http.HTTPStatus.FOUND
    assert not ParentTransaction.objects.filter(pk=parent_transaction.pk).exists()
    assert not Debt.objects.filter(room=room, settled=False).exists()
