import pytest

from apps.account.tests.test_utils import build_image_bytes


@pytest.mark.e2e
class TestEditProfile:
    def test_entering_edit_mode_unlocks_the_fields_without_reloading(self, logged_in_profile_detail_page):
        logged_in_profile_detail_page.expect_fields_locked()
        logged_in_profile_detail_page.mark_sheet("before-edit")

        logged_in_profile_detail_page.enter_edit_mode()

        logged_in_profile_detail_page.expect_fields_editable()
        # A marker set before the click can only survive if the very same element is still there,
        # so this fails the moment entering edit mode starts fetching a new page or fragment.
        assert logged_in_profile_detail_page.read_sheet_marker() == "before-edit"

    def test_entering_edit_mode_does_not_move_the_rows(self, logged_in_profile_detail_page):
        # A phone viewport stacks the header, where the swap from one button to two shows up as
        # height: it caught a 2px shift that the desktop layout hid.
        logged_in_profile_detail_page.page.set_viewport_size({"width": 390, "height": 844})
        offset_before = logged_in_profile_detail_page.profile_section_offset()

        logged_in_profile_detail_page.enter_edit_mode()

        # Anything the header only shows while editing would push every row down the page.
        assert logged_in_profile_detail_page.profile_section_offset() == offset_before

    def test_user_can_edit_name_and_email(self, logged_in_profile_detail_page, profile_user, profile_detail_path):
        logged_in_profile_detail_page.enter_edit_mode()

        new_name = "Updated E2E Name"
        new_email = "updated-e2e@yamsa.local"
        logged_in_profile_detail_page.fill_name(new_name)
        logged_in_profile_detail_page.fill_email(new_email)
        logged_in_profile_detail_page.save()

        # Saving swaps the sheet in place — the profile URL never changes.
        assert logged_in_profile_detail_page.page.url.endswith(profile_detail_path)
        logged_in_profile_detail_page.expect_fields_locked()
        logged_in_profile_detail_page.expect_name(new_name)
        logged_in_profile_detail_page.expect_email(new_email)

        profile_user.refresh_from_db()
        assert profile_user.name == new_name
        assert profile_user.email == new_email

    def test_cancelling_restores_the_stored_values(self, logged_in_profile_detail_page, profile_user):
        original_name = profile_user.name

        logged_in_profile_detail_page.enter_edit_mode()
        logged_in_profile_detail_page.fill_name("Discarded Name")
        logged_in_profile_detail_page.cancel_edit_mode()

        logged_in_profile_detail_page.expect_fields_locked()
        logged_in_profile_detail_page.expect_name(original_name)

        profile_user.refresh_from_db()
        assert profile_user.name == original_name

    def test_user_can_toggle_webpush_notification_preference(self, logged_in_profile_detail_page, profile_user):
        profile_user.refresh_from_db()
        current_preference = profile_user.wants_to_receive_webpush_notifications
        new_preference = not current_preference

        logged_in_profile_detail_page.expect_notifications_radio_checked(wants_notifications=current_preference)
        logged_in_profile_detail_page.enter_edit_mode()

        logged_in_profile_detail_page.choose_wants_notifications(wants_notifications=new_preference)
        logged_in_profile_detail_page.save()

        logged_in_profile_detail_page.expect_notifications_radio_checked(wants_notifications=new_preference)

        profile_user.refresh_from_db()
        assert profile_user.wants_to_receive_webpush_notifications == new_preference

    def test_photo_dialog_uploads_without_touching_the_profile(self, logged_in_profile_detail_page, profile_user):
        original_name = profile_user.name

        logged_in_profile_detail_page.open_photo_dialog()
        logged_in_profile_detail_page.expect_photo_dialog_offers(delete=False)
        # The input posts itself through htmx, which only sends the file when hx-encoding is set.
        logged_in_profile_detail_page.upload_photo_from_dialog("avatar.png", build_image_bytes())

        logged_in_profile_detail_page.expect_photo_present()
        # The photo has its own cycle: it neither needs edit mode nor saves the rest of the sheet.
        logged_in_profile_detail_page.expect_fields_locked()

        profile_user.refresh_from_db()
        assert profile_user.profile_picture
        assert profile_user.name == original_name

    def test_photo_dialog_deletes_the_stored_photo(self, logged_in_profile_detail_page, profile_user):
        logged_in_profile_detail_page.open_photo_dialog()
        logged_in_profile_detail_page.upload_photo_from_dialog("avatar.png", build_image_bytes())

        logged_in_profile_detail_page.open_photo_dialog()
        logged_in_profile_detail_page.expect_photo_dialog_offers(delete=True)
        logged_in_profile_detail_page.delete_photo_from_dialog()

        logged_in_profile_detail_page.expect_no_photo()

        profile_user.refresh_from_db()
        assert not profile_user.profile_picture

    def test_photo_dialog_closes_again(self, logged_in_profile_detail_page):
        logged_in_profile_detail_page.open_photo_dialog()
        logged_in_profile_detail_page.close_photo_dialog()

    def test_guest_has_no_edit_option_on_own_profile(self, logged_in_guest_detail_page):
        logged_in_guest_detail_page.expect_edit_button_hidden()
