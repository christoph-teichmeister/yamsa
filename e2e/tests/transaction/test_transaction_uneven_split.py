from collections.abc import Callable
from decimal import Decimal

import pytest
from django.urls import reverse
from playwright.sync_api import Page

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.debt.models import Debt
from apps.room.models import Room
from apps.transaction.models import ChildTransaction, ParentTransaction
from e2e.tests.transaction.conftest import GROCERIES


@pytest.fixture
def flatmate(room: Room) -> User:
    flatmate = UserFactory()
    room.users.add(flatmate)
    return flatmate


@pytest.mark.e2e
class TestTransactionUnevenSplit:
    def test_one_hundred_across_three_is_booked_to_the_cent_and_every_debtor_owes_their_share(
        self,
        open_create_form: Callable,
        room: Room,
        profile_user: User,
        roommate: User,
        flatmate: User,
        page: Page,
    ) -> None:
        create_page = open_create_form()
        create_page.fill_required_fields(description="Hüttenabend", amount="100.00")
        create_page.choose_category(GROCERIES)

        create_page.submit()
        page.wait_for_url(lambda url: url.endswith(reverse("transaction:list", kwargs={"room_slug": room.slug})))

        parent_transaction = ParentTransaction.objects.get(room=room, description="Hüttenabend")
        shares = {
            child.paid_for.name: child.value
            for child in ChildTransaction.objects.filter(parent_transaction=parent_transaction).select_related(
                "paid_for"
            )
        }
        assert sorted(shares.values()) == [Decimal("33.33"), Decimal("33.33"), Decimal("33.34")]
        assert sum(shares.values()) == Decimal("100.00")
        assert set(shares) == {profile_user.name, roommate.name, flatmate.name}
        debts = {
            (debt.debitor.name, debt.creditor.name, debt.value)
            for debt in Debt.objects.filter(room=room, settled=False).select_related("debitor", "creditor")
        }
        assert debts == {
            (name, profile_user.name, share) for name, share in shares.items() if name != profile_user.name
        }
