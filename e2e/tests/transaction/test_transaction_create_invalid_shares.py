from collections.abc import Callable

import pytest
from django.urls import reverse
from playwright.sync_api import Page

from apps.account.models import User
from apps.debt.models import Debt
from apps.room.models import Room
from apps.transaction.models import ParentTransaction
from e2e.tests.transaction.conftest import GROCERIES


@pytest.mark.e2e
class TestTransactionCreateInvalidShares:
    def test_a_negative_share_is_not_booked(
        self, open_create_form: Callable, room: Room, profile_user: User, roommate: User, page: Page
    ) -> None:
        create_page = open_create_form()
        create_page.fill_required_fields(description="Negativ", amount="30.00")
        create_page.choose_category(GROCERIES)
        create_page.set_share(profile_user.name, "40.00")
        create_page.set_share(roommate.name, "-10.00")

        create_page.submit()
        page.wait_for_timeout(500)

        assert page.url.endswith(reverse("transaction:create", kwargs={"room_slug": room.slug}))
        assert not ParentTransaction.objects.filter(room=room, description="Negativ").exists()
        assert not Debt.objects.filter(room=room).exists()

    def test_shares_that_are_all_zero_are_not_booked(
        self, open_create_form: Callable, room: Room, profile_user: User, roommate: User, page: Page
    ) -> None:
        create_page = open_create_form()
        create_page.fill_required_fields(description="Alles null", amount="30.00")
        create_page.choose_category(GROCERIES)
        create_page.set_share(profile_user.name, "0")
        create_page.set_share(roommate.name, "0")

        create_page.submit()
        page.wait_for_timeout(500)

        assert page.url.endswith(reverse("transaction:create", kwargs={"room_slug": room.slug}))
        assert not ParentTransaction.objects.filter(room=room, description="Alles null").exists()
