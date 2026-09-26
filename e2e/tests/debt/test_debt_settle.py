import pytest
from django.urls import reverse

from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.debt.models import Debt
from e2e.conftest import _login
from e2e.pages.debt_list_page import DebtListPage


@pytest.fixture
def open_debt(room_with_open_debt):
    return Debt.objects.get(room=room_with_open_debt)


@pytest.fixture
def debt_list_as(page, base_url, room_with_open_debt):
    def _open(user) -> DebtListPage:
        _login(page, base_url, user.email, DEFAULT_PASSWORD)
        debt_list_page = DebtListPage(
            page, base_url, reverse("debt:list", kwargs={"room_slug": room_with_open_debt.slug})
        )
        debt_list_page.navigate()
        return debt_list_page

    return _open


@pytest.mark.e2e
class TestDebtSettle:
    def test_the_debtor_can_mark_a_debt_as_paid(self, debt_list_as, roommate, profile_user, open_debt):
        debt_list_page = debt_list_as(roommate)
        debt_list_page.expect_row(open_debt.id, text=f"You owe {profile_user.name}", amount="12.50")

        debt_list_page.open_settle_confirmation(open_debt.id)
        debt_list_page.confirm_settlement()

        debt_list_page.expect_settled(open_debt.id)
        debt_list_page.expect_all_settled_badge()
        open_debt.refresh_from_db()
        assert open_debt.settled
        assert open_debt.settled_at is not None

    def test_cancelling_the_confirmation_leaves_the_debt_open(self, debt_list_as, roommate, open_debt):
        debt_list_page = debt_list_as(roommate)

        debt_list_page.open_settle_confirmation(open_debt.id)
        debt_list_page.cancel_settlement()

        debt_list_page.expect_open_for_debtor(open_debt.id)
        open_debt.refresh_from_db()
        assert not open_debt.settled

    def test_the_creditor_cannot_settle_on_the_debtors_behalf(self, debt_list_as, profile_user, roommate, open_debt):
        debt_list_page = debt_list_as(profile_user)

        debt_list_page.expect_row(open_debt.id, text=f"{roommate.name} owes you", amount="12.50")
        debt_list_page.expect_open_for_creditor(open_debt.id)
