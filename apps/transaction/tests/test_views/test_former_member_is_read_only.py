import http
from decimal import Decimal

import pytest
from bs4 import BeautifulSoup
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.room.models import Room
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.models.constants import FORMER_MEMBER_MESSAGE
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


@pytest.fixture
def transaction_of_a_former_member(room: Room, user: User, guest_user: User) -> ParentTransaction:
    parent_transaction, _ = create_parent_transaction_with_optimisation(
        room=room, paid_by=guest_user, paid_for_tuple=(user, guest_user)
    )
    room.users.remove(guest_user)
    return parent_transaction


@pytest.fixture
def transaction_of_members(room: Room, user: User, guest_user: User) -> ParentTransaction:
    parent_transaction, _ = create_parent_transaction_with_optimisation(
        room=room, paid_by=user, paid_for_tuple=(user, guest_user)
    )
    return parent_transaction


@pytest.mark.parametrize("as_payer", [True, False])
def test_involves_former_member_covers_payer_and_debtor(
    room: Room, user: User, guest_user: User, as_payer: bool
) -> None:
    paid_by, paid_for = (guest_user, user) if as_payer else (user, guest_user)
    parent_transaction, _ = create_parent_transaction_with_optimisation(
        room=room, paid_by=paid_by, paid_for_tuple=(paid_for,)
    )
    assert parent_transaction.involves_former_member is False

    room.users.remove(guest_user)

    assert parent_transaction.involves_former_member is True


def test_edit_view_refuses_get(
    authenticated_client: Client, room: Room, transaction_of_a_former_member: ParentTransaction
) -> None:
    response = authenticated_client.get(
        reverse("transaction:edit", kwargs={"room_slug": room.slug, "pk": transaction_of_a_former_member.pk})
    )

    assert response.status_code == http.HTTPStatus.FORBIDDEN


def test_edit_view_refuses_post_and_changes_nothing(
    authenticated_client: Client, room: Room, user: User, transaction_of_a_former_member: ParentTransaction
) -> None:
    before = transaction_of_a_former_member.description

    response = authenticated_client.post(
        reverse("transaction:edit", kwargs={"room_slug": room.slug, "pk": transaction_of_a_former_member.pk}),
        data={"description": "Changed", "paid_by": user.id},
    )

    assert response.status_code == http.HTTPStatus.FORBIDDEN
    transaction_of_a_former_member.refresh_from_db()
    assert transaction_of_a_former_member.description == before


def test_edit_view_still_opens_for_members(
    authenticated_client: Client, room: Room, transaction_of_members: ParentTransaction
) -> None:
    response = authenticated_client.get(
        reverse("transaction:edit", kwargs={"room_slug": room.slug, "pk": transaction_of_members.pk})
    )

    assert response.status_code == http.HTTPStatus.OK


def test_parent_transaction_delete_is_refused(
    authenticated_client: Client, room: Room, transaction_of_a_former_member: ParentTransaction
) -> None:
    response = authenticated_client.post(
        reverse(
            "transaction:parent-transaction-delete",
            kwargs={"room_slug": room.slug, "pk": transaction_of_a_former_member.pk},
        )
    )

    assert response.status_code == http.HTTPStatus.FORBIDDEN
    assert ParentTransaction.objects.filter(pk=transaction_of_a_former_member.pk).exists()


def test_child_transaction_delete_is_refused(
    authenticated_client: Client, room: Room, transaction_of_a_former_member: ParentTransaction
) -> None:
    share = transaction_of_a_former_member.child_transactions.first()

    response = authenticated_client.post(
        reverse("transaction:child-transaction-delete", kwargs={"room_slug": room.slug, "pk": share.pk})
    )

    assert response.status_code == http.HTTPStatus.FORBIDDEN
    assert ChildTransaction.objects.filter(pk=share.pk).exists()


def test_child_transaction_create_is_refused(
    authenticated_client: Client, room: Room, user: User, transaction_of_a_former_member: ParentTransaction
) -> None:
    shares_before = transaction_of_a_former_member.child_transactions.count()

    response = authenticated_client.post(
        reverse("transaction:child-transaction-create", kwargs={"room_slug": room.slug}),
        data={"parent_transaction": transaction_of_a_former_member.pk, "paid_for": user.id, "value": Decimal(5)},
    )

    assert response.status_code == http.HTTPStatus.FORBIDDEN
    assert transaction_of_a_former_member.child_transactions.count() == shares_before


def test_detail_is_read_only_and_says_why(
    authenticated_client: Client, room: Room, transaction_of_a_former_member: ParentTransaction
) -> None:
    response = authenticated_client.get(
        reverse("transaction:detail", kwargs={"room_slug": room.slug, "pk": transaction_of_a_former_member.pk})
    )

    page = BeautifulSoup(response.content.decode(), "html5lib")
    edit_button = page.find("button", attrs={"aria-label": "Edit expense"})
    assert edit_button.has_attr("disabled")
    assert not edit_button.has_attr("hx-get")
    assert str(FORMER_MEMBER_MESSAGE) in page.get_text()
    assert page.select(".transaction-breakdown-item[role=button]") == []


def test_detail_stays_editable_for_members(
    authenticated_client: Client, room: Room, transaction_of_members: ParentTransaction
) -> None:
    response = authenticated_client.get(
        reverse("transaction:detail", kwargs={"room_slug": room.slug, "pk": transaction_of_members.pk})
    )

    page = BeautifulSoup(response.content.decode(), "html5lib")
    edit_button = page.find("button", attrs={"aria-label": "Edit expense"})
    assert not edit_button.has_attr("disabled")
    assert edit_button.has_attr("hx-get")
    assert str(FORMER_MEMBER_MESSAGE) not in page.get_text()
    assert len(page.select(".transaction-breakdown-item[role=button]")) == 2
