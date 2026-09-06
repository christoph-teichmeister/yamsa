import re

from playwright.sync_api import expect

from e2e.pages.base_page import BasePage


class AccountSecurityPage(BasePage):
    """The security settings, reached from the profile's security section."""

    def expect_loaded(self):
        expect(self.page.get_by_role("heading", name="Security settings")).to_be_visible()

    def expect_passkey_registration_offered(self):
        expect(self.page.locator("#passkey-name")).to_be_visible()
        expect(self.page.locator("#passkey-reg-btn")).to_be_visible()
        expect(self.page.locator("#passkey-delete-form")).to_have_count(0)

    def expect_registration_error_hidden(self):
        expect(self.page.locator("#passkey-reg-result")).to_be_hidden()

    def open_change_password(self):
        self.page.locator("button[hx-get*='change-password']").click()
        # hx-push-url only lands after the swap, so the URL has to be awaited rather than read.
        expect(self.page).to_have_url(re.compile(r"/change-password/"))

    def go_back_to_profile(self):
        self.page.locator("[data-back-to-profile]").click()
        expect(self.page).to_have_url(re.compile(r"/detail/"))
