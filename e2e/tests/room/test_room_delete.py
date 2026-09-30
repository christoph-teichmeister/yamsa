import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.room.models import Room
from e2e.pages.room_detail_page import RoomDetailPage


@pytest.mark.e2e
class TestRoomDelete:
    def test_a_closed_room_can_be_deleted_for_good(self, logged_in_room_detail_page, shared_room, page) -> None:
        Room.objects.filter(id=shared_room.id).update(status=Room.StatusChoices.CLOSED)
        logged_in_room_detail_page.navigate()

        logged_in_room_detail_page.delete_room()

        expect(page.locator("#room-sheet")).to_have_count(0)
        assert not Room.objects.filter(id=shared_room.id).exists()

    def test_deleting_a_room_leaves_its_url_behind(
        self, logged_in_room_detail_page, shared_room, page, base_url
    ) -> None:
        Room.objects.filter(id=shared_room.id).update(status=Room.StatusChoices.CLOSED)
        logged_in_room_detail_page.navigate()

        logged_in_room_detail_page.delete_room()

        # A reload must land on the dashboard, not on the deleted room's address.
        expect(page).to_have_url(f"{base_url}{reverse('core:welcome')}")
        response = page.reload()
        assert response.status == 200

    def test_an_open_room_offers_no_deletion(self, logged_in_room_detail_page: RoomDetailPage) -> None:
        logged_in_room_detail_page.expect_status("Open")

        logged_in_room_detail_page.expect_no_delete_option()
