import pytest
from playwright.sync_api import expect

from apps.account.tests.constants import DEFAULT_PASSWORD


@pytest.mark.e2e
class TestChangePassword:
    def test_the_reveal_toggle_shows_and_hides_the_password(self, logged_in_change_password_page):
        password_page = logged_in_change_password_page
        password_page.expect_loaded()
        assert password_page.field_type("old_password") == "password"

        password_page.toggle_reveal("old_password")

        assert password_page.field_type("old_password") == "text"
        assert password_page.toggle_label("old_password") == "Hide password"

        password_page.toggle_reveal("old_password")

        assert password_page.field_type("old_password") == "password"
        assert password_page.toggle_label("old_password") == "Show password"

    def test_a_wrong_current_password_is_reported_on_its_own_field(self, logged_in_change_password_page):
        logged_in_change_password_page.fill_passwords(current="not-my-password", new="a-brand-new-password")

        logged_in_change_password_page.save()

        logged_in_change_password_page.expect_field_error("old_password", "Your current password is incorrect")

    def test_a_mismatched_confirmation_is_reported_on_the_confirmation(self, logged_in_change_password_page):
        logged_in_change_password_page.fill_passwords(
            current=DEFAULT_PASSWORD, new="a-brand-new-password", confirmation="something-else"
        )

        logged_in_change_password_page.save()

        logged_in_change_password_page.expect_field_error("new_password_confirmation", "Passwords do not match")

    def test_saving_returns_to_the_profile_without_signing_the_user_out(
        self, logged_in_change_password_page, profile_detail_path
    ):
        logged_in_change_password_page.fill_passwords(current=DEFAULT_PASSWORD, new="a-brand-new-password")

        logged_in_change_password_page.save_and_expect_the_profile(profile_detail_path)

        # The view logs the user back in, which is what the form's note promises.
        expect(logged_in_change_password_page.page.locator("#profile-sheet")).to_be_visible()
