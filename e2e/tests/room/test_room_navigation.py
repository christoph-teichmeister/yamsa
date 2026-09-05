import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.account.tests.constants import DEFAULT_PASSWORD
from e2e.pages.base_page import BasePage
from e2e.pages.login_page import LoginPage


@pytest.mark.e2e
class TestRoomNavigation:
    def test_a_room_card_can_be_opened_with_the_keyboard(self, page, base_url, profile_user, shared_room):
        # The card is a div with role="button": Enter only reaches it through the delegated handler
        # in apps/static/js/navigation.js, which is what this guards. htmx cannot do it itself -
        # its trigger filters need eval, which the CSP forbids.
        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.navigate()
        login_page.login(profile_user.email, DEFAULT_PASSWORD)

        dashboard = BasePage(page, base_url, reverse("core:welcome"))
        dashboard.navigate()

        # Addressed by its target URL rather than by position: the side menu renders before
        # #base-content and its entries carry the same marker, so "the first one" is a menu row.
        room_url = reverse("transaction:list", kwargs={"room_slug": shared_room.slug})
        card = page.locator(f'.room-overview-card[hx-get="{room_url}"]')
        expect(card).to_have_count(1)

        card.focus()
        page.keyboard.press("Enter")

        page.wait_for_url(f"**{room_url}")
