import pytest

from apps.account.tests.test_utils import build_image_bytes


@pytest.mark.e2e
class TestEditProfile:
    def test_the_actions_stay_disabled_until_a_field_changes(self, logged_in_profile_detail_page):
        logged_in_profile_detail_page.expect_fields_editable()
        # Nothing has changed yet, so there is nothing to save or to throw away.
        logged_in_profile_detail_page.expect_actions_disabled()

        logged_in_profile_detail_page.fill_name("Updated E2E Name")

        logged_in_profile_detail_page.expect_actions_enabled()

    def test_typing_never_leaves_the_page(self, logged_in_profile_detail_page):
        logged_in_profile_detail_page.mark_sheet("before-typing")

        logged_in_profile_detail_page.fill_name("Updated E2E Name")

        # A marker set before typing can only survive if the very same element is still there, so
        # this fails the moment editing starts fetching a page or a fragment.
        assert logged_in_profile_detail_page.read_sheet_marker() == "before-typing"

    def test_user_can_edit_name_and_email(self, logged_in_profile_detail_page, profile_user, profile_detail_path):
        new_name = "Updated E2E Name"
        new_email = "updated-e2e@yamsa.local"
        logged_in_profile_detail_page.fill_name(new_name)
        logged_in_profile_detail_page.fill_email(new_email)
        logged_in_profile_detail_page.save()

        # Saving swaps the sheet in place — the profile URL never changes.
        assert logged_in_profile_detail_page.page.url.endswith(profile_detail_path)
        logged_in_profile_detail_page.expect_actions_disabled()
        logged_in_profile_detail_page.expect_name(new_name)
        logged_in_profile_detail_page.expect_email(new_email)

        profile_user.refresh_from_db()
        assert profile_user.name == new_name
        assert profile_user.email == new_email

    def test_discarding_restores_the_stored_values(self, logged_in_profile_detail_page, profile_user):
        original_name = profile_user.name

        logged_in_profile_detail_page.fill_name("Discarded Name")
        logged_in_profile_detail_page.expect_actions_enabled()
        logged_in_profile_detail_page.discard()

        logged_in_profile_detail_page.expect_actions_disabled()
        logged_in_profile_detail_page.expect_name(original_name)

        profile_user.refresh_from_db()
        assert profile_user.name == original_name

    def test_user_can_toggle_webpush_notification_preference(self, logged_in_profile_detail_page, profile_user):
        profile_user.refresh_from_db()
        current_preference = profile_user.wants_to_receive_webpush_notifications
        new_preference = not current_preference

        logged_in_profile_detail_page.expect_notifications_radio_checked(wants_notifications=current_preference)

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
        # The photo has its own cycle, so the sheet around it is untouched and still pristine.
        logged_in_profile_detail_page.expect_actions_disabled()

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

    def test_photo_dialog_opens_from_the_camera_badge(self, logged_in_profile_detail_page):
        # The badge overhangs the avatar button, so it carries the same trigger of its own.
        logged_in_profile_detail_page.open_photo_dialog_via_badge()

    def test_the_photo_hover_hint_does_not_stick_after_a_click(self, logged_in_profile_detail_page):
        logged_in_profile_detail_page.move_pointer_away()
        logged_in_profile_detail_page.expect_photo_hover_hint(visible=False)

        logged_in_profile_detail_page.hover_photo()
        logged_in_profile_detail_page.expect_photo_hover_hint(visible=True)

        logged_in_profile_detail_page.open_photo_dialog()
        logged_in_profile_detail_page.close_photo_dialog()
        logged_in_profile_detail_page.move_pointer_away()

        # A mouse click leaves the button focused; keying the hint off :focus-within left the
        # overlay covering the photo from then on.
        logged_in_profile_detail_page.expect_photo_hover_hint(visible=False)

    def test_a_guest_gets_no_editable_sheet_of_their_own(self, logged_in_guest_detail_page):
        logged_in_guest_detail_page.expect_actions_absent()

    def test_navigating_from_the_security_rows_morphs_instead_of_replacing(self, logged_in_profile_detail_page):
        # The security rows ask for hx-swap="morph:innerHTML". That only takes effect while the
        # idiomorph extension both registers and is activated under the name it registers with —
        # miss either and htmx quietly replaces the shell instead, throwing away focus and scroll.
        logged_in_profile_detail_page.mark_body_shell()

        logged_in_profile_detail_page.open_change_password_via_security_row()

        assert logged_in_profile_detail_page.body_shell_survived()
