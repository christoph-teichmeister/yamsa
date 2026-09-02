from playwright.sync_api import Page

from e2e.pages.base_page import BasePage


class AccountEditPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page, base_url="", path=None)

    def fill_name(self, name: str):
        self.page.fill("#name", name)

    def fill_email(self, email: str):
        self.page.fill("#email", email)

    def choose_wants_notifications(self, *, wants_notifications: bool):
        checkbox = self.page.locator("#wants_to_receive_webpush_notifications")
        if wants_notifications:
            checkbox.check()
        else:
            checkbox.uncheck()

    def submit(self):
        with self.page.expect_response(lambda response: "/update/" in response.url):
            self.page.locator("#save-profile-button").click()
