import pytest

from e2e.pages.account_edit_page import AccountEditPage


@pytest.mark.e2e
class TestEditProfile:
    def test_user_can_edit_name_and_email(self, logged_in_profile_detail_page, profile_user, profile_detail_path):
        logged_in_profile_detail_page.go_to_edit()

        edit_page = AccountEditPage(logged_in_profile_detail_page.page)
        new_name = "Updated E2E Name"
        new_email = "updated-e2e@yamsa.local"
        edit_page.fill_name(new_name)
        edit_page.fill_email(new_email)
        edit_page.submit()

        logged_in_profile_detail_page.page.wait_for_url(
            f"{logged_in_profile_detail_page.base_url}{profile_detail_path}"
        )
        logged_in_profile_detail_page.expect_name(new_name)
        logged_in_profile_detail_page.expect_email(new_email)

        profile_user.refresh_from_db()
        assert profile_user.name == new_name
        assert profile_user.email == new_email

    def test_user_can_toggle_webpush_notification_preference(
        self, logged_in_profile_detail_page, profile_user, profile_detail_path
    ):
        profile_user.refresh_from_db()
        current_preference = profile_user.wants_to_receive_webpush_notifications
        new_preference = not current_preference

        logged_in_profile_detail_page.expect_notifications_radio_checked(wants_notifications=current_preference)
        logged_in_profile_detail_page.go_to_edit()

        edit_page = AccountEditPage(logged_in_profile_detail_page.page)
        edit_page.choose_wants_notifications(wants_notifications=new_preference)
        edit_page.submit()

        logged_in_profile_detail_page.page.wait_for_url(
            f"{logged_in_profile_detail_page.base_url}{profile_detail_path}"
        )
        logged_in_profile_detail_page.expect_notifications_radio_checked(wants_notifications=new_preference)

        profile_user.refresh_from_db()
        assert profile_user.wants_to_receive_webpush_notifications == new_preference

    def test_guest_has_no_edit_option_on_own_profile(self, logged_in_guest_detail_page):
        logged_in_guest_detail_page.expect_edit_button_hidden()
