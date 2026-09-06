import re

from playwright.sync_api import expect

from e2e.pages.base_page import BasePage


class ChangePasswordPage(BasePage):
    """The password form, reached from the security settings."""

    def expect_loaded(self):
        expect(self.page.get_by_role("heading", name="Change your password")).to_be_visible()

    def fill_passwords(self, *, current: str, new: str, confirmation: str | None = None):
        self.page.locator("#old_password").fill(current)
        self.page.locator("#new_password").fill(new)
        self.page.locator("#new_password_confirmation").fill(confirmation if confirmation is not None else new)

    def save(self):
        with self.page.expect_response(lambda response: "/change-password/" in response.url):
            self.page.locator("#save-password-button").click()

    def save_and_expect_the_profile(self, profile_detail_path: str):
        """A successful save answers with a redirect, so the pushed URL is the profile's."""

        self.page.locator("#save-password-button").click()
        expect(self.page).to_have_url(re.compile(rf"{re.escape(profile_detail_path)}$"))

    def toggle_reveal(self, field_id: str):
        self.page.locator(f"[data-password-toggle='{field_id}']").click()

    def field_type(self, field_id: str) -> str:
        return self.page.locator(f"#{field_id}").get_attribute("type")

    def toggle_label(self, field_id: str) -> str:
        return self.page.locator(f"[data-password-toggle='{field_id}']").get_attribute("aria-label")

    def expect_field_error(self, field_id: str, message: str):
        expect(self.page.locator(f"#{field_id}Error")).to_have_text(message)
