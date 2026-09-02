from playwright.sync_api import expect

from e2e.pages.base_page import BasePage


class AccountDetailPage(BasePage):
    def go_to_edit(self):
        with self.page.expect_response(lambda response: "/update/" in response.url):
            self.page.locator("#edit-profile-button").click()

    def expect_name(self, name: str):
        expect(self.page.locator("#profile-name")).to_have_text(name)

    def expect_email(self, email: str):
        expect(self.page.locator("#profile-email")).to_have_text(email)

    def expect_edit_button_visible(self):
        expect(self.page.locator("#edit-profile-button")).to_be_visible()

    def expect_edit_button_hidden(self):
        expect(self.page.locator("#edit-profile-button")).to_have_count(0)

    def expect_security_section_visible(self):
        expect(self.page.locator("#security-section")).to_be_visible()

    def expect_security_section_hidden(self):
        expect(self.page.locator("#security-section")).to_have_count(0)

    def expect_guest_mode_banner_visible(self):
        expect(self.page.locator("#guest-mode-banner")).to_be_visible()

    def expect_notifications_radio_checked(self, *, wants_notifications: bool):
        checkbox = self.page.locator("#wants_to_receive_webpush_notifications")
        if wants_notifications:
            expect(checkbox).to_be_checked()
        else:
            expect(checkbox).not_to_be_checked()
