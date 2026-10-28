from collections.abc import Callable
from http import HTTPStatus

import pytest
from django.urls import reverse
from playwright.sync_api import Page

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.debt.models import Debt
from apps.room.models import Room
from apps.transaction.models import Category, ChildTransaction, ParentTransaction
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

    @pytest.mark.parametrize("case", ["negative", "length_mismatch", "outsider"])
    def test_a_crafted_post_past_the_browser_checks_is_not_booked(
        self, open_create_form: Callable, room: Room, profile_user: User, roommate: User, case: str
    ) -> None:
        # The browser stops a negative amount (min=0) and only offers room members, so these
        # requests are sent by hand: the server has to refuse them on its own.
        create_page = open_create_form()
        paid_for = [str(profile_user.id), str(roommate.id)]
        values = ["40.00", "-10.00"]
        if case == "length_mismatch":
            values = ["30.00"]
        if case == "outsider":
            paid_for = [str(profile_user.id), str(UserFactory().id)]
            values = ["15.00", "15.00"]

        response = create_page.post(
            reverse("transaction:create", kwargs={"room_slug": room.slug}),
            {
                "description": "Gebastelt",
                "further_notes": "",
                "paid_by": str(profile_user.id),
                "paid_at": "2026-03-14 12:00:00",
                "currency": str(room.preferred_currency.id),
                "category": str(Category.objects.get(slug=GROCERIES).id),
                "room": str(room.id),
                "room_slug": str(room.slug),
                "paid_for": paid_for,
                "value": values,
                "total_value": "30.00",
                "reference_total_value": "30.00",
            },
        )

        assert response.status == HTTPStatus.OK  # re-rendered with errors, not redirected
        assert not ParentTransaction.objects.filter(room=room, description="Gebastelt").exists()
        assert not ChildTransaction.objects.filter(parent_transaction__room=room).exists()

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
