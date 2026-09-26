from decimal import Decimal

import pytest
from django.urls import reverse

from apps.account.tests.factories import UserFactory
from apps.debt.models import Debt
from apps.transaction.models import ChildTransaction, ParentTransaction
from e2e.tests.transaction.conftest import GROCERIES


@pytest.fixture
def flatmate(room):
    flatmate = UserFactory()
    room.users.add(flatmate)
    return flatmate


def _booked_shares(room, description: str) -> dict[str, Decimal]:
    parent_transaction = ParentTransaction.objects.get(room=room, description=description)
    return {
        child.paid_for.name: child.value
        for child in ChildTransaction.objects.filter(parent_transaction=parent_transaction).select_related("paid_for")
    }


@pytest.mark.e2e
class TestTransactionSplit:
    def test_a_total_is_split_evenly_with_the_odd_cent_on_the_first_row(
        self, open_create_form, profile_user, roommate, flatmate
    ):
        create_page = open_create_form()

        create_page.set_total("10.00")

        # Row order, which shares() keeps, is what the server's split_amount_exact() hands the
        # remainder out by, so the preview has to put the cent in the same place.
        shares = create_page.shares()
        assert list(shares.values()) == ["3.34", "3.33", "3.33"]
        assert set(shares) == {profile_user.name, roommate.name, flatmate.name}

    def test_a_hand_edited_share_is_booked_as_entered(self, open_create_form, room, profile_user, roommate, page):
        create_page = open_create_form()
        create_page.fill_required_fields(description="Tankfüllung", amount="30.00")
        create_page.choose_category(GROCERIES)

        create_page.set_share(profile_user.name, "10.00")
        create_page.set_share(roommate.name, "20.00")
        create_page.submit()
        page.wait_for_url(lambda url: url.endswith(reverse("transaction:list", kwargs={"room_slug": room.slug})))

        assert _booked_shares(room, "Tankfüllung") == {
            profile_user.name: Decimal("10.00"),
            roommate.name: Decimal("20.00"),
        }
        debt = Debt.objects.get(room=room, settled=False)
        assert (debt.debitor, debt.creditor, debt.value) == (roommate, profile_user, Decimal("20.00"))

    def test_shares_that_outgrow_the_total_raise_it_to_their_sum(
        self, open_create_form, room, profile_user, roommate, page
    ):
        create_page = open_create_form()
        create_page.fill_required_fields(description="Grillabend", amount="30.00")
        create_page.choose_category(GROCERIES)

        # Only the share changes; the total was never touched again, so the shares win.
        create_page.set_share(roommate.name, "25.00")
        create_page.submit()
        page.wait_for_url(lambda url: url.endswith(reverse("transaction:list", kwargs={"room_slug": room.slug})))

        assert _booked_shares(room, "Grillabend") == {
            profile_user.name: Decimal("15.00"),
            roommate.name: Decimal("25.00"),
        }

    def test_changing_the_total_resets_hand_edited_shares(self, open_create_form, profile_user, roommate):
        create_page = open_create_form()
        create_page.set_total("30.00")
        create_page.set_share(roommate.name, "25.00")

        create_page.set_total("40.00")

        create_page.expect_shares({profile_user.name: "20.00", roommate.name: "20.00"})

    def test_removing_a_participant_folds_their_share_into_the_untouched_rows(
        self, open_create_form, profile_user, roommate, flatmate
    ):
        create_page = open_create_form()
        create_page.set_total("30.00")
        create_page.set_share(profile_user.name, "16.00")

        create_page.remove_share(flatmate.name)

        create_page.expect_shares({profile_user.name: "16.00", roommate.name: "14.00"})

    def test_adding_a_participant_rebalances_only_the_untouched_rows(
        self, open_create_form, room, profile_user, roommate, flatmate, page
    ):
        create_page = open_create_form()
        create_page.fill_required_fields(description="Pizzaabend", amount="30.00")
        create_page.choose_category(GROCERIES)
        create_page.remove_share(flatmate.name)
        create_page.set_share(roommate.name, "20.00")

        create_page.add_participant(flatmate.name)

        # The new row joins the untouched one in sharing what the edited row leaves over.
        create_page.expect_shares({profile_user.name: "5.00", roommate.name: "20.00", flatmate.name: "5.00"})
        create_page.submit()
        page.wait_for_url(lambda url: url.endswith(reverse("transaction:list", kwargs={"room_slug": room.slug})))
        assert _booked_shares(room, "Pizzaabend") == {
            profile_user.name: Decimal("5.00"),
            roommate.name: Decimal("20.00"),
            flatmate.name: Decimal("5.00"),
        }
