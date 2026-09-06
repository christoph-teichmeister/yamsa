from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect

from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.currency.tests.factories import CurrencyFactory
from apps.debt.models import Debt
from apps.room.models import Room
from apps.room.tests.factories import RoomFactory
from apps.transaction.tests.factories import ParentTransactionFactory
from e2e.pages.dashboard_page import DashboardPage
from e2e.pages.login_page import LoginPage


def _add_transaction(*, room, user, paid_at: datetime):
    return ParentTransactionFactory(room=room, paid_by=user, currency=room.preferred_currency, paid_at=paid_at)


def _room_with_balance(
    *,
    name: str,
    owner,
    roommate,
    currency,
    owed_by_owner: Decimal | None = None,
    owed_to_owner: Decimal | None = None,
    status: str = Room.StatusChoices.OPEN,
    last_transaction_at: datetime | None = None,
):
    room = RoomFactory(created_by=owner, name=name, status=status)
    room.users.add(owner, roommate)
    if owed_by_owner is not None:
        Debt.objects.create(room=room, debitor=owner, creditor=roommate, currency=currency, value=owed_by_owner)
    if owed_to_owner is not None:
        Debt.objects.create(room=room, debitor=roommate, creditor=owner, currency=currency, value=owed_to_owner)
    if last_transaction_at is not None:
        _add_transaction(room=room, user=owner, paid_at=last_transaction_at)
    return room


def _closed_room_with_debt(*, owner, roommate, currency):
    return _room_with_balance(
        name="Closed Room",
        owner=owner,
        roommate=roommate,
        currency=currency,
        owed_by_owner=Decimal("99.00"),
        status=Room.StatusChoices.CLOSED,
    )


def _url_of(room):
    return reverse(Room.dashboard_viewname_for(room.status), kwargs={"room_slug": room.slug})


@pytest.fixture
def euro(transactional_db):
    return CurrencyFactory(sign="€")


@pytest.fixture
def rooms_by_recency(profile_user, roommate, euro):
    """Four open rooms whose latest transaction runs opposite to their open balance.

    The room with the largest debt was last used a month ago and the settled one five minutes
    ago, so the expected order below is the exact reverse of what a balance-driven dashboard
    would show - an ordering that fell back on the amounts would fail every assertion on it.
    """
    now = timezone.now()
    big_debt = _room_with_balance(
        name="Big Debt Room",
        owner=profile_user,
        roommate=roommate,
        currency=euro,
        owed_by_owner=Decimal("1234.50"),
        last_transaction_at=now - timedelta(days=30),
    )
    small_debt = _room_with_balance(
        name="Small Debt Room",
        owner=profile_user,
        roommate=roommate,
        currency=euro,
        owed_by_owner=Decimal("12.50"),
        last_transaction_at=now - timedelta(days=1),
    )
    receiving = _room_with_balance(
        name="Receiving Room",
        owner=profile_user,
        roommate=roommate,
        currency=euro,
        owed_to_owner=Decimal("7.50"),
        last_transaction_at=now - timedelta(hours=1),
    )
    settled = _room_with_balance(
        name="Settled Room",
        owner=profile_user,
        roommate=roommate,
        currency=euro,
        last_transaction_at=now - timedelta(minutes=5),
    )
    return {"big_debt": big_debt, "small_debt": small_debt, "receiving": receiving, "settled": settled}


@pytest.fixture
def open_dashboard(page, base_url, profile_user):
    """Log in and load the dashboard, on call rather than on fixture setup.

    A fixture that navigated straight away would race the test's own data: pytest resolves
    fixtures in signature order, so the page could load before the rooms exist and every
    assertion would then be about an empty dashboard.
    """

    def _open(as_user=None) -> DashboardPage:
        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.navigate()
        login_page.login((as_user or profile_user).email, DEFAULT_PASSWORD)

        dashboard = DashboardPage(page, base_url, reverse("core:welcome"))
        dashboard.navigate()
        return dashboard

    return _open


@pytest.mark.e2e
class TestDashboardRoomList:
    def test_rooms_are_ordered_by_their_latest_transaction(self, rooms_by_recency, open_dashboard):
        open_dashboard().expect_room_order(["Settled Room", "Receiving Room", "Small Debt Room", "Big Debt Room"])

    def test_a_new_transaction_lifts_its_room_to_the_top(self, rooms_by_recency, profile_user, open_dashboard):
        dashboard = open_dashboard()
        dashboard.expect_room_order(["Settled Room", "Receiving Room", "Small Debt Room", "Big Debt Room"])

        _add_transaction(room=rooms_by_recency["big_debt"], user=profile_user, paid_at=timezone.now())
        dashboard.navigate()

        dashboard.expect_room_order(["Big Debt Room", "Settled Room", "Receiving Room", "Small Debt Room"])

    def test_a_room_without_transactions_starts_at_the_top(
        self, rooms_by_recency, profile_user, roommate, euro, open_dashboard
    ):
        # A room created just now has nothing to show yet and must not open at the bottom.
        brand_new_room = _room_with_balance(name="Brand New Room", owner=profile_user, roommate=roommate, currency=euro)

        dashboard = open_dashboard()

        dashboard.expect_room_order(
            ["Brand New Room", "Settled Room", "Receiving Room", "Small Debt Room", "Big Debt Room"]
        )
        # Nothing was ever paid here, so the card has no last use to name.
        dashboard.expect_no_last_used(_url_of(brand_new_room))

    def test_each_card_names_when_its_room_was_last_used(self, rooms_by_recency, open_dashboard):
        dashboard = open_dashboard()

        dashboard.expect_last_used(_url_of(rooms_by_recency["settled"]), "5\xa0minutes ago")
        dashboard.expect_last_used(_url_of(rooms_by_recency["receiving"]), "1\xa0hour ago")
        # One unit, not naturaltime's "4 weeks, 2 days ago".
        dashboard.expect_last_used(_url_of(rooms_by_recency["big_debt"]), "4\xa0weeks ago")

    def test_each_card_names_its_direction_and_amount(self, rooms_by_recency, open_dashboard):
        dashboard = open_dashboard()

        dashboard.expect_amount(_url_of(rooms_by_recency["big_debt"]), label="You owe", value="1,234.50€")
        dashboard.expect_amount(_url_of(rooms_by_recency["receiving"]), label="You get back", value="7.50€")
        dashboard.expect_settled(_url_of(rooms_by_recency["settled"]))

    def test_the_summary_sums_the_open_rooms_per_direction(self, rooms_by_recency, open_dashboard):
        open_dashboard().expect_summary(owed=["1,247.00€"], received=["7.50€"])

    def test_cards_of_the_users_own_rooms_carry_no_status_badge(self, rooms_by_recency, open_dashboard):
        # The "Open" section heading already says it; repeating it per card only costs width.
        open_dashboard().expect_no_status_badge(_url_of(rooms_by_recency["big_debt"]))

    def test_a_closed_room_shows_neither_its_debt_nor_a_settled_hint(
        self, profile_user, roommate, euro, open_dashboard
    ):
        closed_room = _closed_room_with_debt(owner=profile_user, roommate=roommate, currency=euro)

        dashboard = open_dashboard()
        dashboard.expand_section("closedRooms")

        dashboard.expect_no_amount(_url_of(closed_room))
        dashboard.expect_no_summary()

    def test_closed_rooms_stay_collapsed_until_the_section_is_opened(
        self, profile_user, roommate, euro, open_dashboard
    ):
        closed_room = _closed_room_with_debt(owner=profile_user, roommate=roommate, currency=euro)

        dashboard = open_dashboard()

        dashboard.expect_section_is_collapsed("closedRooms")
        dashboard.expand_section("closedRooms")
        expect(dashboard.card_for(_url_of(closed_room))).to_be_visible()

    def test_a_user_without_open_balances_gets_no_summary(self, shared_room, open_dashboard):
        open_dashboard().expect_no_summary()

    def test_foreign_rooms_are_shown_two_per_row_with_their_status(
        self, profile_user, roommate, euro, superuser, open_dashboard
    ):
        # A superuser sees every room of the instance, none of which is theirs. The section mixes
        # open and closed rooms, so each tile has to say which of the two it is.
        now = timezone.now()
        open_room = _room_with_balance(
            name="Foreign Open Room",
            owner=profile_user,
            roommate=roommate,
            currency=euro,
            last_transaction_at=now - timedelta(minutes=5),
        )
        closed_room = _room_with_balance(
            name="Foreign Closed Room",
            owner=profile_user,
            roommate=roommate,
            currency=euro,
            owed_by_owner=Decimal("99.00"),
            status=Room.StatusChoices.CLOSED,
            last_transaction_at=now - timedelta(days=30),
        )

        dashboard = open_dashboard(superuser)

        dashboard.expect_section_is_collapsed("otherRooms")
        dashboard.expand_section("otherRooms")
        dashboard.expect_side_by_side(_url_of(open_room), _url_of(closed_room))
        dashboard.expect_status_badge(_url_of(open_room), str(Room.StatusChoices.OPEN.label))
        dashboard.expect_status_badge(_url_of(closed_room), str(Room.StatusChoices.CLOSED.label))
        # Foreign rooms carry no balance for the superuser, tile or not.
        dashboard.expect_no_amount(_url_of(closed_room))
