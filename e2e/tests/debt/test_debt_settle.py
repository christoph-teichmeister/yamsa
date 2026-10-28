from collections.abc import Callable

import pytest

from apps.account.models import User
from apps.debt.models import Debt


@pytest.mark.e2e
class TestDebtSettle:
    def test_the_debtor_can_mark_a_debt_as_paid(
        self, debt_list_as: Callable, roommate: User, profile_user: User, open_debt: Debt
    ) -> None:
        debt_list_page = debt_list_as(roommate)
        debt_list_page.expect_row(open_debt.id, text=f"You owe {profile_user.name}", amount="12.50")

        debt_list_page.open_settle_confirmation(open_debt.id)
        debt_list_page.confirm_settlement()

        debt_list_page.expect_settled(open_debt.id)
        debt_list_page.expect_all_settled_badge()
        open_debt.refresh_from_db()
        assert open_debt.settled
        assert open_debt.settled_at is not None

    def test_cancelling_the_confirmation_leaves_the_debt_open(
        self, debt_list_as: Callable, roommate: User, open_debt: Debt
    ) -> None:
        debt_list_page = debt_list_as(roommate)

        debt_list_page.open_settle_confirmation(open_debt.id)
        debt_list_page.cancel_settlement()

        debt_list_page.expect_open_for_debtor(open_debt.id)
        open_debt.refresh_from_db()
        assert not open_debt.settled

    def test_the_creditor_cannot_settle_on_the_debtors_behalf(
        self, debt_list_as: Callable, profile_user: User, roommate: User, open_debt: Debt
    ) -> None:
        debt_list_page = debt_list_as(profile_user)

        debt_list_page.expect_row(open_debt.id, text=f"{roommate.name} owes you", amount="12.50")
        debt_list_page.expect_open_for_creditor(open_debt.id)
