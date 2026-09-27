from decimal import Decimal

import pytest
from django.db import connection
from django.urls import reverse
from playwright.sync_api import expect

from apps.account.tests.factories import UserFactory
from apps.debt.models import Debt
from apps.debt.services.debt_optimise_service import DebtOptimiseService
from apps.room.models import Room
from apps.transaction.models import Category, ChildTransaction, ParentTransaction
from apps.transaction.tests.factories import ParentTransactionFactory
from e2e.pages.transaction_detail_page import TransactionDetailPage
from e2e.pages.transaction_edit_page import TransactionEditPage
from e2e.tests.transaction.conftest import GROCERIES


@pytest.fixture
def flatmate(room):
    flatmate = UserFactory()
    room.users.add(flatmate)
    return flatmate


@pytest.fixture
def parent_transaction(room, profile_user, roommate, flatmate):
    """30.00 paid by the profile user and split evenly with the roommate, the flatmate left out.

    The flatmate is a room member without a share, so the form has someone to add.
    """
    parent_transaction = ParentTransactionFactory(
        room=room,
        paid_by=profile_user,
        currency=room.preferred_currency,
        description="Wocheneinkauf",
        category=Category.objects.get(slug=GROCERIES),
    )
    for participant in (profile_user, roommate):
        ChildTransaction.objects.create(parent_transaction=parent_transaction, paid_for=participant, value="15.00")
    DebtOptimiseService.process(room_id=room.id)
    # live_server writes from its own thread, and on SQLite this test's connection would keep the
    # rows above locked against the writes the edit form issues.
    connection.close()
    return parent_transaction


@pytest.fixture
def open_edit_form(page, base_url, room, parent_transaction, logged_in):
    def _open() -> TransactionEditPage:
        logged_in()
        edit_page = TransactionEditPage(
            page,
            base_url,
            reverse("transaction:edit", kwargs={"room_slug": room.slug, "pk": parent_transaction.id}),
        )
        edit_page.navigate()
        return edit_page

    return _open


def _booked_shares(parent_transaction: ParentTransaction) -> dict[str, Decimal]:
    return {
        child.paid_for.name: child.value
        for child in ChildTransaction.objects.filter(parent_transaction=parent_transaction).select_related("paid_for")
    }


def _open_debts(room: Room) -> set[tuple[str, str, Decimal]]:
    """Who owes whom how much, by name, so a failing assertion reads without looking up ids."""
    return {
        (debt.debitor.name, debt.creditor.name, debt.value)
        for debt in Debt.objects.filter(room=room, settled=False).select_related("debitor", "creditor")
    }


@pytest.mark.e2e
class TestTransactionEdit:
    def test_the_detail_page_opens_the_form_with_the_saved_shares(
        self, page, base_url, room, parent_transaction, profile_user, roommate, logged_in
    ):
        logged_in()
        detail_path = reverse("transaction:detail", kwargs={"room_slug": room.slug, "pk": parent_transaction.id})
        TransactionDetailPage(page, base_url, detail_path).navigate()

        page.get_by_role("button", name="Edit expense").click()

        edit_path = reverse("transaction:edit", kwargs={"room_slug": room.slug, "pk": parent_transaction.id})
        page.wait_for_url(lambda url: url.endswith(edit_path))
        edit_page = TransactionEditPage(page, base_url, edit_path)
        edit_page.expect_shares({profile_user.name: "15.00", roommate.name: "15.00"})
        edit_page.expect_shares_locked(locked=False)

    def test_a_new_total_locks_the_shares_and_is_split_evenly_on_save(
        self, open_edit_form, room, parent_transaction, profile_user, roommate, page
    ):
        edit_page = open_edit_form()

        edit_page.set_total("50.00")
        edit_page.expect_shares_locked(locked=True)
        edit_page.save()
        self._wait_for_detail_page(page, room, parent_transaction)

        assert _booked_shares(parent_transaction) == {
            profile_user.name: Decimal("25.00"),
            roommate.name: Decimal("25.00"),
        }
        assert _open_debts(room) == {(roommate.name, profile_user.name, Decimal("25.00"))}

    def test_restoring_the_total_unlocks_the_shares_again(self, open_edit_form):
        edit_page = open_edit_form()

        edit_page.set_total("50.00")
        edit_page.set_total("30.00")

        edit_page.expect_shares_locked(locked=False)

    def test_an_edited_share_is_booked_and_moves_the_debt(
        self, open_edit_form, room, parent_transaction, profile_user, roommate, page
    ):
        edit_page = open_edit_form()

        edit_page.set_share(profile_user.name, "5.00")
        edit_page.set_share(roommate.name, "25.00")
        edit_page.save()
        self._wait_for_detail_page(page, room, parent_transaction)

        assert _booked_shares(parent_transaction) == {
            profile_user.name: Decimal("5.00"),
            roommate.name: Decimal("25.00"),
        }
        assert _open_debts(room) == {(roommate.name, profile_user.name, Decimal("25.00"))}

    def test_a_new_payer_turns_the_debt_around(
        self, open_edit_form, room, parent_transaction, profile_user, roommate, page
    ):
        edit_page = open_edit_form()

        edit_page.set_paid_by(roommate.name)
        edit_page.save()
        self._wait_for_detail_page(page, room, parent_transaction)

        assert ParentTransaction.objects.get(pk=parent_transaction.pk).paid_by == roommate
        assert _open_debts(room) == {(profile_user.name, roommate.name, Decimal("15.00"))}

    def test_a_participant_added_while_editing_gets_a_share_and_a_debt(
        self, open_edit_form, room, parent_transaction, profile_user, roommate, flatmate, page
    ):
        edit_page = open_edit_form()

        edit_page.add_participant(flatmate.name, "12.00")
        edit_page.save()
        self._wait_for_detail_page(page, room, parent_transaction)

        assert _booked_shares(parent_transaction) == {
            profile_user.name: Decimal("15.00"),
            roommate.name: Decimal("15.00"),
            flatmate.name: Decimal("12.00"),
        }
        assert _open_debts(room) == {
            (roommate.name, profile_user.name, Decimal("15.00")),
            (flatmate.name, profile_user.name, Decimal("12.00")),
        }

    def test_removing_a_saved_share_drops_it_from_the_debts(
        self, open_edit_form, room, parent_transaction, profile_user, roommate
    ):
        edit_page = open_edit_form()

        edit_page.remove_saved_share(roommate.name)

        # The share is gone on the server the moment the confirmation is accepted, without a save;
        # a visitor who leaves the form here must not find the old debt still standing.
        edit_page.expect_shares({profile_user.name: "15.00"})
        assert _booked_shares(parent_transaction) == {profile_user.name: Decimal("15.00")}
        assert _open_debts(room) == set()

    def test_dismissing_the_removal_keeps_the_share(self, open_edit_form, parent_transaction, profile_user, roommate):
        edit_page = open_edit_form()

        edit_page.remove_saved_share(roommate.name, confirm=False)

        edit_page.expect_shares({profile_user.name: "15.00", roommate.name: "15.00"})
        assert _booked_shares(parent_transaction) == {
            profile_user.name: Decimal("15.00"),
            roommate.name: Decimal("15.00"),
        }

    def test_removing_the_last_share_deletes_the_transaction(
        self, open_edit_form, room, parent_transaction, profile_user, roommate, page
    ):
        edit_page = open_edit_form()

        edit_page.remove_saved_share(roommate.name)
        edit_page.expect_shares({profile_user.name: "15.00"})
        edit_page.remove_saved_share(profile_user.name)

        page.wait_for_url(lambda url: url.endswith(reverse("transaction:list", kwargs={"room_slug": room.slug})))
        assert not ParentTransaction.objects.filter(pk=parent_transaction.pk).exists()
        assert _open_debts(room) == set()

    def test_deleting_the_transaction_clears_its_debt(self, open_edit_form, room, parent_transaction, page):
        edit_page = open_edit_form()

        edit_page.delete_transaction()

        page.wait_for_url(lambda url: url.endswith(reverse("transaction:list", kwargs={"room_slug": room.slug})))
        assert not ParentTransaction.objects.filter(pk=parent_transaction.pk).exists()
        assert not ChildTransaction.objects.filter(parent_transaction_id=parent_transaction.pk).exists()
        assert _open_debts(room) == set()

    def test_dismissing_the_deletion_keeps_the_transaction(
        self, open_edit_form, room, parent_transaction, profile_user, roommate
    ):
        edit_page = open_edit_form()

        edit_page.delete_transaction(confirm=False)

        edit_page.expect_shares({profile_user.name: "15.00", roommate.name: "15.00"})
        assert ParentTransaction.objects.filter(pk=parent_transaction.pk).exists()
        assert _open_debts(room) == {(roommate.name, profile_user.name, Decimal("15.00"))}

    def test_a_closed_room_offers_no_edit(self, page, base_url, room, parent_transaction, logged_in):
        Room.objects.filter(pk=room.pk).update(status=Room.StatusChoices.CLOSED)
        connection.close()
        logged_in()

        detail_path = reverse("transaction:detail", kwargs={"room_slug": room.slug, "pk": parent_transaction.id})
        TransactionDetailPage(page, base_url, detail_path).navigate()

        expect(page.get_by_role("button", name="Edit expense")).to_be_disabled()

    @staticmethod
    def _wait_for_detail_page(page, room, parent_transaction):
        # Saving redirects to the detail page; reading the DB before that lands would race the
        # request still in flight.
        detail_path = reverse("transaction:detail", kwargs={"room_slug": room.slug, "pk": parent_transaction.id})
        page.wait_for_url(lambda url: url.endswith(detail_path))
