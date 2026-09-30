import http
from decimal import Decimal
from unittest import mock

import pytest
from django.urls import reverse

from apps.debt.models import Debt
from apps.news.models import News
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation
from apps.transaction.tests.factories import ChildTransactionFactory, ParentTransactionFactory
from apps.webpush.utils import Notification

pytestmark = pytest.mark.django_db


def test_post_closed_room_is_rejected(authenticated_client, closed_room, user, guest_user):
    parent_transaction = ParentTransactionFactory(room=closed_room, paid_by=user)
    child_transaction = ChildTransactionFactory(
        parent_transaction=parent_transaction,
        paid_for=user,
        value=Decimal(5),
    )
    ChildTransactionFactory(
        parent_transaction=parent_transaction,
        paid_for=guest_user,
        value=Decimal(5),
    )

    response = authenticated_client.post(
        reverse(
            "transaction:child-transaction-delete",
            kwargs={"room_slug": closed_room.slug, "pk": child_transaction.pk},
        ),
    )

    assert response.status_code == http.HTTPStatus.FORBIDDEN
    assert ChildTransaction.objects.filter(pk=child_transaction.pk).exists()


def test_removing_a_share_recalculates_the_debts_without_a_save(authenticated_client, room, user, guest_user):
    parent_transaction, (_, guest_share) = create_parent_transaction_with_optimisation(
        room=room, paid_by=user, paid_for_tuple=(user, guest_user)
    )
    assert Debt.objects.filter(room=room, settled=False, debitor=guest_user).exists()

    response = authenticated_client.post(
        reverse(
            "transaction:child-transaction-delete",
            kwargs={"room_slug": room.slug, "pk": guest_share.pk},
        ),
    )

    assert response.status_code == http.HTTPStatus.FOUND
    assert ParentTransaction.objects.filter(pk=parent_transaction.pk).exists()
    assert not Debt.objects.filter(room=room, settled=False).exists()


def test_removing_the_last_share_reports_what_the_transaction_carried(authenticated_client, room, user, guest_user):
    parent_transaction, (guest_share,) = create_parent_transaction_with_optimisation(
        room=room, paid_by=user, paid_for_tuple=(guest_user,)
    )
    amount_and_sign = f"({parent_transaction.value}{parent_transaction.currency.sign})"

    with mock.patch.object(Notification, "send_to_user") as mocked_send:
        authenticated_client.post(
            reverse(
                "transaction:child-transaction-delete",
                kwargs={"room_slug": room.slug, "pk": guest_share.pk},
            ),
        )

    assert not ParentTransaction.objects.filter(pk=parent_transaction.pk).exists()
    assert not Debt.objects.filter(room=room, settled=False).exists()
    news = News.objects.get(room=room, type=News.TypeChoices.TRANSACTION_DELETED)
    assert amount_and_sign in news.message
    assert guest_user in [call.args[0] for call in mocked_send.call_args_list]
