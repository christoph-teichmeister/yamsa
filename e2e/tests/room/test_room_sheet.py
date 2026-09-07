import pytest


@pytest.mark.e2e
class TestRoomSheet:
    def test_entering_edit_mode_unlocks_the_fields_without_reloading(self, logged_in_room_detail_page):
        logged_in_room_detail_page.expect_fields_locked()
        logged_in_room_detail_page.mark_sheet("before-edit")

        logged_in_room_detail_page.enter_edit_mode()

        logged_in_room_detail_page.expect_fields_editable()
        # A marker set before the click can only survive if the very same element is still there,
        # so this fails the moment entering edit mode starts fetching a new page or fragment.
        assert logged_in_room_detail_page.read_sheet_marker() == "before-edit"

    def test_entering_edit_mode_does_not_move_the_rows(self, logged_in_room_detail_page):
        # A phone viewport stacks the header, where the swap from one button to two shows up as
        # height — the same measurement that caught a 2px shift on the profile.
        logged_in_room_detail_page.page.set_viewport_size({"width": 390, "height": 844})
        offset_before = logged_in_room_detail_page.details_section_offset()

        logged_in_room_detail_page.enter_edit_mode()

        assert logged_in_room_detail_page.details_section_offset() == offset_before

    def test_renaming_the_room_swaps_the_sheet_in_place(self, logged_in_room_detail_page):
        logged_in_room_detail_page.enter_edit_mode()
        logged_in_room_detail_page.fill_name("Renamed by e2e")

        logged_in_room_detail_page.save()

        # The sheet comes back reading, with the saved value — and the URL never changed.
        logged_in_room_detail_page.expect_heading("Renamed by e2e")
        logged_in_room_detail_page.expect_name("Renamed by e2e")
        logged_in_room_detail_page.expect_fields_locked()
        logged_in_room_detail_page.expect_url_is_the_room()

    def test_cancelling_restores_the_stored_values(self, logged_in_room_detail_page, shared_room):
        logged_in_room_detail_page.enter_edit_mode()
        logged_in_room_detail_page.fill_name("Typed but never saved")

        logged_in_room_detail_page.cancel_edit_mode()

        logged_in_room_detail_page.expect_name(shared_room.name)
        logged_in_room_detail_page.expect_fields_locked()

    def test_closing_a_settled_room_leaves_nothing_to_edit(self, logged_in_room_detail_page):
        logged_in_room_detail_page.expect_status("Open")

        logged_in_room_detail_page.close_room()

        logged_in_room_detail_page.expect_status("Closed")
        # A closed room has no editable field, so it offers no edit mode either.
        logged_in_room_detail_page.expect_edit_button_absent()

        logged_in_room_detail_page.reopen_room()

        logged_in_room_detail_page.expect_status("Open")
        logged_in_room_detail_page.expect_edit_button_visible()
