import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.account.models import User
from apps.account.tests.constants import DEFAULT_PASSWORD
from e2e.conftest import _login
from e2e.pages.account_detail_page import AccountDetailPage
from e2e.pages.room_people_page import RoomPeoplePage
from e2e.pages.room_share_page import RoomSharePage


@pytest.fixture
def people_page(page, base_url, profile_user, shared_room):
    _login(page, base_url, profile_user.email, DEFAULT_PASSWORD)
    roster_page = RoomPeoplePage(page, base_url, reverse("account:list", kwargs={"room_slug": shared_room.slug}))
    roster_page.navigate()
    return roster_page


@pytest.mark.e2e
class TestGuestInvite:
    def test_an_added_guest_joins_the_roster(self, people_page, shared_room, profile_user):
        people_page.add_guest("Alex aus der Küche")

        people_page.expect_member("Alex aus der Küche")
        guest = User.objects.get(name="Alex aus der Küche")
        assert guest.is_guest
        assert guest.created_by == profile_user
        assert shared_room.users.filter(id=guest.id).exists()

    def test_a_guest_claims_their_seat_through_the_share_link(self, people_page, shared_room, base_url, new_context):
        people_page.add_guest("Alex aus der Küche")
        people_page.expect_member("Alex aus der Küche")
        share_url = people_page.share_url()

        # A fresh context: the visitor arrives without the inviter's session.
        guest_page = new_context().new_page()
        share_page = RoomSharePage(guest_page, share_url)
        share_page.navigate()
        share_page.claim_guest_seat("Alex aus der Küche")

        guest_page.wait_for_url(
            lambda url: url.endswith(reverse("transaction:list", kwargs={"room_slug": shared_room.slug}))
        )

        # This context started without a session and an anonymous visitor is sent to the
        # login page, so reaching the guest's profile proves the claim signed them in.
        guest = User.objects.get(name="Alex aus der Küche")
        profile_page = AccountDetailPage(guest_page, base_url, reverse("account:detail", kwargs={"pk": guest.id}))
        profile_page.navigate()
        profile_page.expect_guest_mode_banner_visible()

    def test_a_room_without_guests_offers_no_seat_to_claim(self, shared_room, page, base_url):
        share_url = f"{base_url}{reverse('room:share', kwargs={'share_hash': shared_room.share_hash})}"

        share_page = RoomSharePage(page, share_url)
        share_page.navigate()

        expect(page.locator("#userSelect")).to_have_count(0)
        expect(page.get_by_text("No guests have been invited yet.", exact=False)).to_be_visible()
