import http
from unittest import mock

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.debt.models import Debt
from apps.news.models import News
from apps.room.models import Room
from apps.transaction.models import ParentTransaction
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation
from apps.transaction.tests.factories import ParentTransactionFactory
from apps.webpush.utils import Notification

pytestmark = pytest.mark.django_db


def test_post_closed_room_is_rejected(authenticated_client: Client, closed_room: Room, user: User) -> None:
    parent_transaction = ParentTransactionFactory(room=closed_room, paid_by=user)

    response = authenticated_client.post(
        reverse(
            "transaction:parent-transaction-delete",
            kwargs={"room_slug": closed_room.slug, "pk": parent_transaction.pk},
        ),
    )

    assert response.status_code == http.HTTPStatus.FORBIDDEN
    assert ParentTransaction.objects.filter(pk=parent_transaction.pk).exists()


def test_deleting_a_transaction_clears_the_debt_it_caused(
    authenticated_client: Client, room: Room, user: User, guest_user: User
) -> None:
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


def test_deleting_a_transaction_reports_what_it_carried(
    authenticated_client: Client, room: Room, user: User, guest_user: User
) -> None:
    parent_transaction, _ = create_parent_transaction_with_optimisation(
        room=room, paid_by=user, paid_for_tuple=(user, guest_user)
    )
    amount_and_sign = f"({parent_transaction.value}{parent_transaction.currency.sign})"

    with mock.patch.object(Notification, "send_to_user") as mocked_send:
        authenticated_client.post(
            reverse(
                "transaction:parent-transaction-delete",
                kwargs={"room_slug": room.slug, "pk": parent_transaction.pk},
            ),
        )

    news = News.objects.get(room=room, type=News.TypeChoices.TRANSACTION_DELETED)
    assert amount_and_sign in news.message
    assert guest_user in [call.args[0] for call in mocked_send.call_args_list]
