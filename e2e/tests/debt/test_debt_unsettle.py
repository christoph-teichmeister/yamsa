from collections.abc import Callable

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.account.models import User
from apps.debt.models import Debt
from apps.room.models import Room


@pytest.mark.e2e
class TestDebtUnsettle:
    def test_settling_stamps_the_server_date_and_unsettling_clears_it(
        self, debt_list_as: Callable, roommate: User, open_debt: Debt, room_with_open_debt: Room
    ) -> None:
        debt_list_page = debt_list_as(roommate)

        debt_list_page.open_settle_confirmation(open_debt.id)
        debt_list_page.confirm_settlement()
        debt_list_page.expect_settled(open_debt.id)

        open_debt.refresh_from_db()
        assert open_debt.settled_at == timezone.localdate()

        settle_path = reverse("debt:settle", kwargs={"room_slug": room_with_open_debt.slug, "pk": open_debt.id})
        response = debt_list_page.post(settle_path)

        assert response.status == 302
        open_debt.refresh_from_db()
        assert open_debt.settled is False
        assert open_debt.settled_at is None
        debt_list_page.navigate()
        debt_list_page.expect_open_for_debtor(open_debt.id)

    def test_a_date_sent_with_the_request_is_ignored(
        self, debt_list_as: Callable, roommate: User, open_debt: Debt, room_with_open_debt: Room
    ) -> None:
        debt_list_page = debt_list_as(roommate)
        settle_path = reverse("debt:settle", kwargs={"room_slug": room_with_open_debt.slug, "pk": open_debt.id})

        debt_list_page.post(settle_path, {"settled": "true", "settled_at": "2001-01-01"})

        open_debt.refresh_from_db()
        assert open_debt.settled is True
        assert open_debt.settled_at == timezone.localdate()
