import pytest


@pytest.mark.e2e
class TestRoomSheet:
    def test_the_actions_stay_disabled_until_a_field_changes(self, logged_in_room_detail_page):
        logged_in_room_detail_page.expect_fields_editable()
        # Nothing has changed yet, so there is nothing to save or to throw away.
        logged_in_room_detail_page.expect_actions_disabled()

        logged_in_room_detail_page.fill_name("Renamed by e2e")

        logged_in_room_detail_page.expect_actions_enabled()

    def test_typing_never_leaves_the_page(self, logged_in_room_detail_page):
        logged_in_room_detail_page.mark_sheet("before-typing")

        logged_in_room_detail_page.fill_name("Renamed by e2e")

        # A marker set before typing can only survive if the very same element is still there, so
        # this fails the moment editing starts fetching a page or a fragment.
        assert logged_in_room_detail_page.read_sheet_marker() == "before-typing"

    def test_saving_swaps_the_sheet_in_place(self, logged_in_room_detail_page):
        logged_in_room_detail_page.fill_name("Renamed by e2e")

        logged_in_room_detail_page.save()

        # The sheet comes back with the saved value, pristine again — and the URL never changed.
        logged_in_room_detail_page.expect_heading("Renamed by e2e")
        logged_in_room_detail_page.expect_name("Renamed by e2e")
        logged_in_room_detail_page.expect_actions_disabled()
        logged_in_room_detail_page.expect_url_is_the_room()

    def test_discarding_restores_the_stored_values(self, logged_in_room_detail_page, shared_room):
        logged_in_room_detail_page.fill_name("Typed but never saved")
        logged_in_room_detail_page.expect_actions_enabled()

        logged_in_room_detail_page.discard()

        logged_in_room_detail_page.expect_name(shared_room.name)
        logged_in_room_detail_page.expect_actions_disabled()

    def test_closing_a_settled_room_leaves_nothing_to_edit(self, logged_in_room_detail_page):
        logged_in_room_detail_page.expect_status("Open")

        logged_in_room_detail_page.close_room()

        logged_in_room_detail_page.expect_status("Closed")
        # A closed room has no editable field, so its fields go inert and the actions disappear.
        logged_in_room_detail_page.expect_fields_inert()
        logged_in_room_detail_page.expect_actions_absent()

        logged_in_room_detail_page.reopen_room()

        logged_in_room_detail_page.expect_status("Open")
        logged_in_room_detail_page.expect_actions_present()
