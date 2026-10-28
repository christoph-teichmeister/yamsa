import http

import pytest
from django.urls import reverse
from playwright.sync_api import Page

from apps.account.models import User
from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.account.tests.factories import GuestUserFactory
from apps.room.models import Room
from e2e.conftest import _login
from e2e.pages.room_access_page import RoomAccessPage
from e2e.pages.room_detail_page import RoomDetailPage
from e2e.pages.room_people_page import RoomPeoplePage

PROTECTED_VIEWS = ["room:edit", "room:status", "room:delete", "account:guest-create", "account:list"]


@pytest.fixture
def access_page(page: Page, base_url: str) -> RoomAccessPage:
    return RoomAccessPage(page, base_url)


@pytest.fixture
def room_with_guest(shared_room: Room) -> Room:
    shared_room.users.add(GuestUserFactory())
    return shared_room


@pytest.mark.e2e
class TestRoomAccess:
    @pytest.mark.parametrize("view_name", PROTECTED_VIEWS)
    def test_an_anonymous_visitor_is_sent_to_the_login(
        self, access_page: RoomAccessPage, shared_room: Room, view_name: str
    ) -> None:
        status = access_page.visit(reverse(view_name, kwargs={"room_slug": shared_room.slug}))

        assert status == http.HTTPStatus.OK
        access_page.expect_login_redirect()

    @pytest.mark.parametrize("view_name", PROTECTED_VIEWS)
    def test_a_logged_in_non_member_gets_a_403(
        self,
        access_page: RoomAccessPage,
        page: Page,
        base_url: str,
        unrelated_user: User,
        shared_room: Room,
        view_name: str,
    ) -> None:
        _login(page, base_url, unrelated_user.email, DEFAULT_PASSWORD)

        status = access_page.visit(reverse(view_name, kwargs={"room_slug": shared_room.slug}))

        assert status == http.HTTPStatus.FORBIDDEN

    def test_a_member_can_still_edit_the_room(
        self, logged_in_room_detail_page: RoomDetailPage, shared_room: Room
    ) -> None:
        logged_in_room_detail_page.fill_name("Edited by a member")

        logged_in_room_detail_page.save()

        logged_in_room_detail_page.expect_heading("Edited by a member")
        shared_room.refresh_from_db()
        assert shared_room.name == "Edited by a member"

    def test_a_member_can_still_add_a_user_by_email(
        self, page: Page, base_url: str, profile_user: User, shared_room: Room, unrelated_user: User
    ) -> None:
        _login(page, base_url, profile_user.email, DEFAULT_PASSWORD)
        people_page = RoomPeoplePage(page, base_url, reverse("account:list", kwargs={"room_slug": shared_room.slug}))
        people_page.navigate()

        people_page.add_existing_user(unrelated_user.email)

        people_page.expect_member(unrelated_user.name)
        assert shared_room.users.filter(id=unrelated_user.id).exists()

    @pytest.mark.parametrize("view_name", ["room:dashboard", "room:detail"])
    def test_the_public_pages_show_an_anonymous_visitor_the_guest_picker(
        self, access_page: RoomAccessPage, room_with_guest: Room, view_name: str
    ) -> None:
        access_page.visit(reverse(view_name, kwargs={"room_slug": room_with_guest.slug}))

        access_page.expect_guest_picker()

    @pytest.mark.parametrize("view_name", ["room:dashboard", "room:detail"])
    def test_the_public_pages_show_a_non_member_the_guest_picker(
        self,
        access_page: RoomAccessPage,
        page: Page,
        base_url: str,
        unrelated_user: User,
        room_with_guest: Room,
        view_name: str,
    ) -> None:
        _login(page, base_url, unrelated_user.email, DEFAULT_PASSWORD)

        access_page.visit(reverse(view_name, kwargs={"room_slug": room_with_guest.slug}))

        access_page.expect_guest_picker()

    def test_the_share_link_shows_the_guest_picker(self, access_page: RoomAccessPage, room_with_guest: Room) -> None:
        access_page.visit(reverse("room:share", kwargs={"share_hash": room_with_guest.share_hash}))

        access_page.expect_guest_picker()

    @pytest.mark.parametrize("slug", ["00000000-0000-4000-8000-000000000000", "not-a-uuid"])
    def test_an_unknown_room_slug_is_a_404(self, access_page: RoomAccessPage, slug: str) -> None:
        status = access_page.visit(reverse("room:detail", kwargs={"room_slug": slug}))

        assert status == http.HTTPStatus.NOT_FOUND
