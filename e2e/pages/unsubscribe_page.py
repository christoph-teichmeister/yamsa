from playwright.sync_api import expect

from e2e.pages.base_page import BasePage


class UnsubscribePage(BasePage):
    def expect_confirmation(self) -> None:
        expect(self.page.locator("#confirm-unsubscribe-button")).to_be_visible()

    def confirm(self) -> None:
        self.page.locator("#confirm-unsubscribe-button").click()
        self.page.wait_for_load_state("load")

    def expect_unsubscribed(self) -> None:
        expect(self.page.get_by_text("no longer receiving payment reminders", exact=False)).to_be_visible()
        expect(self.page.locator("#confirm-unsubscribe-button")).to_have_count(0)
