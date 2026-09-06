from decimal import Decimal

import pytest
from django.urls import reverse

from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.currency.tests.factories import CurrencyFactory
from apps.debt.models import Debt
from apps.room.models import Room
from apps.room.tests.factories import RoomFactory
from e2e.pages.dashboard_page import DashboardPage
from e2e.pages.login_page import LoginPage


def _room_with_balance(
    *,
    name: str,
    owner,
    roommate,
    currency,
    owed_by_owner: Decimal | None = None,
    owed_to_owner: Decimal | None = None,
    status: str = Room.StatusChoices.OPEN,
):
    room = RoomFactory(created_by=owner, name=name, status=status)
    room.users.add(owner, roommate)
    if owed_by_owner is not None:
        Debt.objects.create(room=room, debitor=owner, creditor=roommate, currency=currency, value=owed_by_owner)
    if owed_to_owner is not None:
        Debt.objects.create(room=room, debitor=roommate, creditor=owner, currency=currency, value=owed_to_owner)
    return room


def _url_of(room):
    return reverse(Room.dashboard_viewname_for(room.status), kwargs={"room_slug": room.slug})


@pytest.fixture
def euro(transactional_db):
    return CurrencyFactory(sign="€")


@pytest.fixture
def ranked_rooms(profile_user, roommate, euro):
    """One open room per attention rank, created in the order the dashboard has to undo.

    room_qs_for_list falls back to lastmodified_at for rooms without transactions, so the room
    created last arrives first. Creating them best-rank-first means the expected order is the
    exact reverse of what the queryset hands over - a dashboard that only passed the queryset
    through would fail every ordering assertion below.
    """
    big_debt = _room_with_balance(
        name="Big Debt Room", owner=profile_user, roommate=roommate, currency=euro, owed_by_owner=Decimal("1234.50")
    )
    small_debt = _room_with_balance(
        name="Small Debt Room", owner=profile_user, roommate=roommate, currency=euro, owed_by_owner=Decimal("12.50")
    )
    receiving = _room_with_balance(
        name="Receiving Room", owner=profile_user, roommate=roommate, currency=euro, owed_to_owner=Decimal("7.50")
    )
    settled = _room_with_balance(name="Settled Room", owner=profile_user, roommate=roommate, currency=euro)
    return {"big_debt": big_debt, "small_debt": small_debt, "receiving": receiving, "settled": settled}


@pytest.fixture
def open_dashboard(page, base_url, profile_user):
    """Log in and load the dashboard, on call rather than on fixture setup.

    A fixture that navigated straight away would race the test's own data: pytest resolves
    fixtures in signature order, so the page could load before the rooms exist and every
    assertion would then be about an empty dashboard.
    """

    def _open() -> DashboardPage:
        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.navigate()
        login_page.login(profile_user.email, DEFAULT_PASSWORD)

        dashboard = DashboardPage(page, base_url, reverse("core:welcome"))
        dashboard.navigate()
        return dashboard

    return _open


@pytest.mark.e2e
class TestDashboardRoomList:
    def test_rooms_are_ordered_by_what_needs_paying_first(self, ranked_rooms, open_dashboard):
        open_dashboard().expect_room_order(["Big Debt Room", "Small Debt Room", "Receiving Room", "Settled Room"])

    def test_each_card_names_its_direction_and_amount(self, ranked_rooms, open_dashboard):
        dashboard = open_dashboard()

        dashboard.expect_amount(_url_of(ranked_rooms["big_debt"]), label="You owe", value="1,234.50€")
        dashboard.expect_amount(_url_of(ranked_rooms["receiving"]), label="You get back", value="7.50€")
        dashboard.expect_settled(_url_of(ranked_rooms["settled"]))

    def test_the_summary_sums_the_open_rooms_per_direction(self, ranked_rooms, open_dashboard):
        open_dashboard().expect_summary(owed=["1,247.00€"], received=["7.50€"])

    def test_cards_of_the_users_own_rooms_carry_no_status_badge(self, ranked_rooms, open_dashboard):
        # The "Open" section heading already says it; repeating it per card only costs width.
        open_dashboard().expect_no_status_badge(_url_of(ranked_rooms["big_debt"]))

    def test_a_closed_rooms_debt_shows_on_its_card_but_not_in_the_summary(
        self, profile_user, roommate, euro, open_dashboard
    ):
        closed_room = _room_with_balance(
            name="Closed Room",
            owner=profile_user,
            roommate=roommate,
            currency=euro,
            owed_by_owner=Decimal("99.00"),
            status=Room.StatusChoices.CLOSED,
        )

        dashboard = open_dashboard()

        dashboard.expect_amount(_url_of(closed_room), label="You owe", value="99.00€")
        dashboard.expect_no_summary()

    def test_a_user_without_open_balances_gets_no_summary(self, shared_room, open_dashboard):
        open_dashboard().expect_no_summary()
