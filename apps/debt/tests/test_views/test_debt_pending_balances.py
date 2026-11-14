import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.debt.models import Debt
from apps.debt.services.debt_optimise_service import DebtOptimiseService
from apps.room.models import Room
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db

SETTLE_MESSAGES = "apps.debt.views.debt_settle_view.handle_message"
REOPEN_MESSAGES = "apps.debt.views.debt_reopen_view.handle_message"


def settle_url(debt: Debt) -> str:
    return reverse("debt:settle", kwargs={"room_slug": debt.room.slug, "pk": debt.pk})


def reopen_url(debt: Debt) -> str:
    return reverse("debt:reopen", kwargs={"room_slug": debt.room.slug, "pk": debt.pk})


def login(client: Client, who: User) -> Client:
    client.force_login(who)
    return client


class TestBalances:
    def test_a_pending_debt_still_counts_as_open(self, room: Room, pending_debt: Debt, user: User) -> None:
        assert room.debts.filter_open().filter(pk=pending_debt.pk).exists()
        assert Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
            creditor_id=user.id, room_id=room.id, currency_id=pending_debt.currency_id
        ) == pytest.approx(pending_debt.value)
        assert room.can_be_closed is False

    def test_the_optimiser_keeps_the_pending_debt_and_adds_no_duplicate(self, room: Room, pending_debt: Debt) -> None:
        DebtOptimiseService.process(room.id)

        [only] = Debt.objects.filter(room=room)
        assert only.pk == pending_debt.pk
        assert only.awaiting_confirmation is True

    def test_a_new_expense_is_optimised_around_the_pending_debt(
        self, room: Room, pending_debt: Debt, user: User, guest_user: User
    ) -> None:
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))

        rows = Debt.objects.filter(room=room).order_by("pk")
        assert [row.awaiting_confirmation for row in rows] == [True, False]
        assert rows[0].pk == pending_debt.pk
        assert rows[1].value == pending_debt.value

    def test_a_rejected_payment_is_optimised_like_any_open_debt(
        self, client: Client, room: Room, pending_debt: Debt, user: User
    ) -> None:
        login(client, user).post(reopen_url(pending_debt))

        DebtOptimiseService.process(room.id)

        [only] = Debt.objects.filter(room=room)
        assert (only.settled, only.awaiting_confirmation, only.value) == (False, False, pending_debt.value)
