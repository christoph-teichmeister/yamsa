from decimal import Decimal

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.account.tests.factories import UserFactory
from apps.debt.models import Debt
from apps.room.models import Room
from apps.room.tests.factories import RoomFactory
from e2e.conftest import _login
from e2e.pages.dashboard_page import DashboardPage
from e2e.pages.room_people_page import RoomPeoplePage


def _dashboard_url(room):
    return reverse(Room.dashboard_viewname_for(room.status), kwargs={"room_slug": room.slug})


@pytest.fixture
def people_page(page, base_url, profile_user, shared_room):
    _login(page, base_url, profile_user.email, DEFAULT_PASSWORD)
    roster_page = RoomPeoplePage(page, base_url, reverse("account:list", kwargs={"room_slug": shared_room.slug}))
    roster_page.navigate()
    return roster_page


@pytest.mark.e2e
class TestRoomMembers:
    def test_an_existing_user_is_added_by_email(self, people_page, shared_room):
        newcomer = UserFactory(name="Nora Neu")

        people_page.add_existing_user(newcomer.email)

        people_page.expect_member("Nora Neu")
        assert shared_room.users.filter(id=newcomer.id).exists()

    def test_an_unknown_email_is_reported_instead_of_added(self, people_page, shared_room):
        people_page.add_existing_user("niemand@yamsa.local")

        people_page.expect_field_error("Email does not exist")
        assert shared_room.users.count() == 2

    def test_a_roommate_without_expenses_can_be_removed(self, people_page, shared_room, roommate):
        people_page.remove_member(roommate.name)

        people_page.expect_no_member(roommate.name)
        assert not shared_room.users.filter(id=roommate.id).exists()

    def test_a_roommate_with_open_debts_stays(self, people_page, shared_room, profile_user, roommate):
        Debt.objects.create(
            room=shared_room,
            debitor=roommate,
            creditor=profile_user,
            value=Decimal("8.00"),
            currency=shared_room.preferred_currency,
        )

        people_page.remove_member(roommate.name)

        people_page.expect_toast("can not be removed from this room")
        people_page.expect_member(roommate.name)
        assert shared_room.users.filter(id=roommate.id).exists()

    def test_leaving_a_room_takes_it_off_the_dashboard(self, people_page, shared_room, profile_user, page, base_url):
        other_room = RoomFactory(created_by=profile_user, name="Bleibt")
        other_room.users.add(profile_user)

        people_page.remove_member(profile_user.name)

        page.wait_for_url(lambda url: url.endswith(reverse("core:welcome")))
        dashboard_page = DashboardPage(page, base_url, reverse("core:welcome"))
        dashboard_page.navigate()
        # The room they still belong to is the control: without it, an empty dashboard would pass too.
        dashboard_page.expect_room_order([other_room.name])
        expect(dashboard_page.card_for(_dashboard_url(shared_room))).to_have_count(0)
        assert not shared_room.users.filter(id=profile_user.id).exists()
