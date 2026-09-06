import http

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse

from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation
from apps.transaction.tests.factories import ParentTransactionFactory
from apps.transaction.views import TransactionDetailView

pytestmark = pytest.mark.django_db


def test_transaction_detail_shows_receipt_empty_state(client, room, user):
    parent_transaction = ParentTransactionFactory(room=room, paid_by=user, currency=room.preferred_currency)
    client.force_login(user)

    response = client.get(reverse("transaction:detail", kwargs={"room_slug": room.slug, "pk": parent_transaction.pk}))

    assert response.status_code == http.HTTPStatus.OK
    content = response.content.decode()
    assert "No receipts have been attached to this transaction yet." in content


def test_transaction_detail_shows_an_avatar_per_split_participant(
    client, room, user, guest_user, attach_profile_picture
):
    attach_profile_picture(user)
    parent_transaction, _ = create_parent_transaction_with_optimisation(
        room=room,
        paid_by=user,
        paid_for_tuple=(user, guest_user),
    )
    client.force_login(user)

    response = client.get(reverse("transaction:detail", kwargs={"room_slug": room.slug, "pk": parent_transaction.pk}))

    assert response.status_code == http.HTTPStatus.OK
    breakdown = BeautifulSoup(response.content.decode(), "html.parser")
    split_avatars = breakdown.select(".transaction-breakdown-item .avatar")
    assert len(split_avatars) == 2

    rendered_avatars = {
        avatar.find("img")["src"] if avatar.find("img") else avatar.get_text(strip=True) for avatar in split_avatars
    }
    assert rendered_avatars == {user.avatar_url, guest_user.name[:1].upper()}


def test_split_rows_do_not_query_per_participant(room, user, guest_user, django_assert_num_queries):
    """Regression test: the breakdown prints a name and an avatar per row."""
    parent_transaction, _ = create_parent_transaction_with_optimisation(
        room=room,
        paid_by=user,
        paid_for_tuple=(user, guest_user),
    )
    view = TransactionDetailView()
    view.object = parent_transaction

    child_transactions = list(view.child_transactions)

    with django_assert_num_queries(0):
        assert [child_transaction.paid_for.name for child_transaction in child_transactions]
