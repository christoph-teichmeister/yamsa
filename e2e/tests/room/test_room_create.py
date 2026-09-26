import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.currency.tests.factories import CurrencyFactory
from apps.room.models import Room
from e2e.conftest import _login
from e2e.pages.dashboard_page import DashboardPage
from e2e.pages.room_create_page import RoomCreatePage


@pytest.fixture
def currencies(transactional_db):
    return CurrencyFactory(code="EUR", sign="€"), CurrencyFactory(code="CHF", sign="Fr")


@pytest.fixture
def room_create_page(page, base_url, profile_user, currencies):
    _login(page, base_url, profile_user.email, DEFAULT_PASSWORD)
    create_page = RoomCreatePage(page, base_url, reverse("room:create"))
    create_page.navigate()
    return create_page


@pytest.mark.e2e
class TestRoomCreate:
    def test_a_new_room_opens_on_its_own_page(self, room_create_page, profile_user, currencies, page):
        _, swiss_francs = currencies

        room_create_page.fill(name="Hütte am See", description="Wanderwoche", currency_label="CHF (Fr)")
        room_create_page.submit()

        room = Room.objects.get(name="Hütte am See")
        page.wait_for_url(lambda url: url.endswith(reverse("room:detail", kwargs={"room_slug": room.slug})))
        expect(page.locator("#room-name")).to_have_text("Hütte am See")
        assert room.created_by == profile_user
        assert room.preferred_currency == swiss_francs
        assert list(room.users.all()) == [profile_user]

    def test_the_new_room_is_listed_on_the_dashboard(self, room_create_page, page, base_url):
        room_create_page.fill(name="WG Küche", description="Einkäufe")
        room_create_page.submit()
        page.wait_for_url(lambda url: url.endswith("/detail"))

        dashboard_page = DashboardPage(page, base_url, reverse("core:welcome"))
        dashboard_page.navigate()

        dashboard_page.expect_room_order(["WG Küche"])

    def test_a_room_without_a_name_is_not_created(self, room_create_page, page):
        room_create_page.fill(name="", description="Ohne Namen")
        room_create_page.submit()

        # The browser blocks the submit on the field's own required constraint.
        assert page.locator("#name").evaluate("input => input.validity.valueMissing")
        assert page.url.endswith(reverse("room:create"))
        assert not Room.objects.exists()
