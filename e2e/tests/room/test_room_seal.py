import re

import pytest
from django.db import connection
from django.urls import reverse
from playwright.sync_api import Page, expect

from apps.account.tests.test_utils import build_image_bytes
from apps.room.models import Room
from apps.room.room_seal import SEAL_ICONS, default_seal_icon
from e2e.pages.room_detail_page import RoomDetailPage


@pytest.fixture
def default_icon(shared_room: Room) -> str:
    return default_seal_icon(shared_room.slug)


@pytest.fixture
def other_icon(default_icon: str) -> str:
    """A predefined icon that is not the room's default, so picking it is a visible change."""
    return next(icon for icon in SEAL_ICONS if icon != default_icon)


def _stored_seal(room: Room) -> tuple[str, bool]:
    room.refresh_from_db()
    return room.seal_icon, bool(room.seal_image)


@pytest.mark.e2e
class TestRoomSeal:
    def test_a_room_wears_its_default_seal_until_one_is_chosen(
        self, logged_in_room_detail_page: RoomDetailPage, default_icon: str
    ) -> None:
        logged_in_room_detail_page.expect_seal_icon(default_icon)

    def test_a_predefined_icon_can_be_picked(
        self, logged_in_room_detail_page: RoomDetailPage, shared_room: Room, other_icon: str
    ) -> None:
        logged_in_room_detail_page.open_seal_dialog()

        logged_in_room_detail_page.pick_seal_icon(other_icon)

        logged_in_room_detail_page.expect_seal_icon(other_icon)
        assert _stored_seal(shared_room) == (other_icon, False)

    def test_each_icon_is_announced_by_name_and_the_chosen_one_as_pressed(
        self, logged_in_room_detail_page: RoomDetailPage, other_icon: str
    ) -> None:
        logged_in_room_detail_page.open_seal_dialog()
        logged_in_room_detail_page.pick_seal_icon(other_icon)

        logged_in_room_detail_page.open_seal_dialog()

        expect(logged_in_room_detail_page.seal_dialog.get_by_role("button", name="palette2")).to_have_count(0)
        for icon_name in SEAL_ICONS:
            expected = "true" if icon_name == other_icon else "false"
            expect(logged_in_room_detail_page.seal_icon_button(icon_name)).to_have_attribute("aria-pressed", expected)

    def test_picking_an_icon_leaves_the_rest_of_the_sheet_pristine(
        self, logged_in_room_detail_page: RoomDetailPage, other_icon: str
    ) -> None:
        logged_in_room_detail_page.open_seal_dialog()

        logged_in_room_detail_page.pick_seal_icon(other_icon)

        # The seal has its own cycle; the sheet's action row only speaks for its fields.
        logged_in_room_detail_page.expect_actions_disabled()

    def test_a_custom_image_replaces_the_icon(
        self, logged_in_room_detail_page: RoomDetailPage, shared_room: Room, other_icon: str
    ) -> None:
        logged_in_room_detail_page.open_seal_dialog()
        logged_in_room_detail_page.pick_seal_icon(other_icon)

        logged_in_room_detail_page.open_seal_dialog()
        logged_in_room_detail_page.upload_seal_image("seal.png", build_image_bytes())

        logged_in_room_detail_page.expect_seal_image()
        assert _stored_seal(shared_room) == ("", True)

    def test_picking_an_icon_replaces_the_custom_image(
        self, logged_in_room_detail_page: RoomDetailPage, shared_room: Room, other_icon: str
    ) -> None:
        logged_in_room_detail_page.open_seal_dialog()
        logged_in_room_detail_page.upload_seal_image("seal.png", build_image_bytes())

        logged_in_room_detail_page.open_seal_dialog()
        logged_in_room_detail_page.pick_seal_icon(other_icon)

        logged_in_room_detail_page.expect_seal_icon(other_icon)
        assert _stored_seal(shared_room) == (other_icon, False)

    def test_a_file_that_is_no_image_is_refused_in_the_open_dialog(
        self, logged_in_room_detail_page: RoomDetailPage, shared_room: Room
    ) -> None:
        logged_in_room_detail_page.open_seal_dialog()

        logged_in_room_detail_page.upload_seal_image("seal.png", b"not an image at all", mime_type="image/png")

        expect(logged_in_room_detail_page.seal_dialog).to_be_visible()
        expect(logged_in_room_detail_page.seal_dialog).to_contain_text("Upload a valid image.")
        assert _stored_seal(shared_room) == ("", False)

    def test_resetting_brings_back_the_default(
        self, logged_in_room_detail_page: RoomDetailPage, shared_room: Room, default_icon: str, other_icon: str
    ) -> None:
        logged_in_room_detail_page.open_seal_dialog()
        logged_in_room_detail_page.upload_seal_image("seal.png", build_image_bytes())

        logged_in_room_detail_page.open_seal_dialog()
        logged_in_room_detail_page.reset_seal()

        logged_in_room_detail_page.expect_seal_icon(default_icon)
        assert _stored_seal(shared_room) == ("", False)

    def test_a_room_with_its_default_seal_offers_no_reset(self, logged_in_room_detail_page: RoomDetailPage) -> None:
        logged_in_room_detail_page.open_seal_dialog()

        expect(logged_in_room_detail_page.seal_dialog.get_by_role("button", name="Reset to default")).to_have_count(0)

    def test_the_chosen_seal_shows_on_the_rooms_other_pages(
        self, logged_in_room_detail_page: RoomDetailPage, shared_room: Room, other_icon: str
    ) -> None:
        logged_in_room_detail_page.open_seal_dialog()
        logged_in_room_detail_page.pick_seal_icon(other_icon)

        page = logged_in_room_detail_page.page
        page.goto(
            f"{logged_in_room_detail_page.base_url}{reverse('debt:list', kwargs={'room_slug': shared_room.slug})}"
        )

        expect(page.locator("#body .room-seal svg use").first).to_have_attribute(
            "href", re.compile(rf"#{re.escape(other_icon)}$")
        )

    def test_a_closed_room_keeps_its_seal(
        self, page: Page, logged_in_room_detail_page: RoomDetailPage, shared_room: Room
    ) -> None:
        Room.objects.filter(pk=shared_room.pk).update(status=Room.StatusChoices.CLOSED)
        connection.close()
        logged_in_room_detail_page.navigate()

        # A closed room cannot be edited: the sheet's fields go inert, and the seal with them.
        logged_in_room_detail_page.expect_fields_inert()
        expect(page.get_by_role("button", name="Change room seal")).to_be_disabled()
