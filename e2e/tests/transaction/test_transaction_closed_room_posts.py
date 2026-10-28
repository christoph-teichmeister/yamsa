from collections.abc import Callable
from http import HTTPStatus

import pytest
from django.db import connection
from django.urls import reverse
from playwright.sync_api import Page

from apps.account.models import User
from apps.room.models import Room
from apps.room.tests.factories import RoomFactory
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.tests.factories import ParentTransactionFactory
from e2e.pages.transaction_detail_page import TransactionDetailPage


@pytest.fixture
def closed_transaction(room: Room, profile_user: User, roommate: User) -> ParentTransaction:
    parent_transaction = ParentTransactionFactory(room=room, paid_by=profile_user, currency=room.preferred_currency)
    for participant in (profile_user, roommate):
        ChildTransaction.objects.create(parent_transaction=parent_transaction, paid_for=participant, value="10.00")
    Room.objects.filter(pk=room.pk).update(status=Room.StatusChoices.CLOSED)
    connection.close()
    return parent_transaction


@pytest.mark.e2e
class TestTransactionClosedRoomPosts:
    def test_a_closed_room_refuses_edits_and_deletions_sent_by_hand(
        self,
        page: Page,
        base_url: str,
        room: Room,
        closed_transaction: ParentTransaction,
        logged_in: Callable,
    ) -> None:
        logged_in()
        detail_path = reverse("transaction:detail", kwargs={"room_slug": room.slug, "pk": closed_transaction.id})
        detail_page = TransactionDetailPage(page, base_url, detail_path)
        detail_page.navigate()
        share = closed_transaction.child_transactions.first()
        kwargs = {"room_slug": room.slug, "pk": closed_transaction.id}

        edit = detail_page.post(reverse("transaction:edit", kwargs=kwargs), {"description": "Geändert"})
        delete = detail_page.post(reverse("transaction:parent-transaction-delete", kwargs=kwargs))
        delete_share = detail_page.post(
            reverse("transaction:child-transaction-delete", kwargs={"room_slug": room.slug, "pk": share.pk})
        )

        assert {edit.status, delete.status, delete_share.status} == {HTTPStatus.FORBIDDEN}
        assert ParentTransaction.objects.get(pk=closed_transaction.pk).description == closed_transaction.description
        assert ChildTransaction.objects.filter(parent_transaction=closed_transaction).count() == 2

    def test_a_closed_rooms_transaction_cannot_be_reached_through_an_open_room(
        self,
        page: Page,
        base_url: str,
        profile_user: User,
        closed_transaction: ParentTransaction,
        logged_in: Callable,
    ) -> None:
        # The slug in the URL names an open room; the pk belongs to the closed one.
        open_room = RoomFactory(created_by=profile_user)
        open_room.users.add(profile_user)
        connection.close()
        logged_in()
        detail_page = TransactionDetailPage(page, base_url, "/")
        detail_page.navigate()
        share = closed_transaction.child_transactions.first()
        slug = open_room.slug

        edit = detail_page.post(
            reverse("transaction:edit", kwargs={"room_slug": slug, "pk": closed_transaction.id}),
            {"description": "Geändert"},
        )
        delete = detail_page.post(
            reverse("transaction:parent-transaction-delete", kwargs={"room_slug": slug, "pk": closed_transaction.id})
        )
        delete_share = detail_page.post(
            reverse("transaction:child-transaction-delete", kwargs={"room_slug": slug, "pk": share.pk})
        )

        assert {edit.status, delete.status, delete_share.status} == {HTTPStatus.NOT_FOUND}
        assert ParentTransaction.objects.get(pk=closed_transaction.pk).description == closed_transaction.description
        assert ChildTransaction.objects.filter(parent_transaction=closed_transaction).count() == 2
