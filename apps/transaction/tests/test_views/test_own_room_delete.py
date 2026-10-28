import http

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.debt.models import Debt
from apps.room.models import Room
from apps.transaction.models import ParentTransaction
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


class TestOwnRoomStillWorks:
    def test_a_member_still_deletes_a_transaction_of_the_room(
        self, authenticated_client: Client, room: Room, user: User, guest_user: User
    ) -> None:
        transaction_to_delete, _ = create_parent_transaction_with_optimisation(
            room=room, paid_by=user, paid_for_tuple=(guest_user,)
        )

        response = authenticated_client.post(
            reverse(
                "transaction:parent-transaction-delete",
                kwargs={"room_slug": room.slug, "pk": transaction_to_delete.pk},
            )
        )

        assert response.status_code == http.HTTPStatus.FOUND
        assert not ParentTransaction.objects.filter(pk=transaction_to_delete.pk).exists()
        assert not Debt.objects.filter(room=room, settled=False).exists()
