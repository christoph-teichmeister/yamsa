from playwright.sync_api import expect

from e2e.pages.base_page import BasePage


class RoomAccessPage(BasePage):
    """Visits room URLs to see whether the app lets the visitor in, and what it shows a non-member."""

    def visit(self, path: str) -> int:
        self.path = path
        response = self.page.goto(f"{self.base_url}{path}")
        self.page.wait_for_load_state("load")
        return response.status

    def expect_login_redirect(self) -> None:
        assert "/account/login/" in self.page.url

    def expect_guest_picker(self) -> None:
        expect(self.page.locator("#userSelect")).to_be_visible()
