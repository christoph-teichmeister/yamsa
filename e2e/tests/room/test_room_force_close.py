import pytest


@pytest.mark.e2e
class TestRoomForceClose:
    def test_a_room_with_open_debts_asks_before_closing(self, logged_in_room_detail_page, room_with_open_debt):
        logged_in_room_detail_page.navigate()
        logged_in_room_detail_page.expect_status("Open")

        logged_in_room_detail_page.open_force_close_dialog()

        # The dialog has to be in the top layer for its backdrop and Escape to work at all.
        assert logged_in_room_detail_page.force_close_dialog_is_modal()

        logged_in_room_detail_page.dismiss_force_close_dialog()

        # Dismissing must not have closed the room behind the dialog.
        logged_in_room_detail_page.expect_status("Open")

    def test_confirming_closes_the_room_anyway(self, logged_in_room_detail_page, room_with_open_debt):
        logged_in_room_detail_page.navigate()

        logged_in_room_detail_page.open_force_close_dialog()
        logged_in_room_detail_page.confirm_force_close()

        logged_in_room_detail_page.expect_status("Closed")
        logged_in_room_detail_page.expect_edit_button_absent()
