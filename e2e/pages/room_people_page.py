from playwright.sync_api import Locator, expect

from e2e.pages.base_page import BasePage


class RoomPeoplePage(BasePage):
    """The room roster at account:list, and the guest form it leads to."""

    def add_guest(self, name: str) -> None:
        self.page.get_by_role("button", name="Add guest").click()
        self.page.locator("#id_name").fill(name)
        # The roster's own "Add guest" button is gone once the form has replaced it, so the name
        # now matches the form's submit button alone.
        with self.page.expect_response(lambda response: "/guest/create/" in response.url):
            self.page.get_by_role("button", name="Add guest").click()

    def add_existing_user(self, email: str) -> None:
        self.page.get_by_role("button", name="Add existing user").click()
        self.page.locator("#id_email").fill(email)
        with self.page.expect_response(lambda response: "/userconnectiontoroom/create" in response.url):
            self.page.get_by_role("button", name="Add existing user").click()

    def remove_member(self, name: str) -> None:
        # hx-confirm asks through the browser's own confirm(), which Playwright would dismiss.
        self.page.once("dialog", lambda dialog: dialog.accept())
        with self.page.expect_response(lambda response: "/remove-from-room/" in response.url):
            self.member_card(name).get_by_role("button", name="Remove from room").click()

    def member_card(self, name: str) -> Locator:
        return self.page.locator("#body article").filter(has_text=name)

    def expect_member(self, name: str) -> None:
        expect(self.member_card(name)).to_have_count(1)

    def expect_no_member(self, name: str) -> None:
        expect(self.member_card(name)).to_have_count(0)

    def expect_field_error(self, message: str) -> None:
        expect(self.page.locator("#body form p.text-danger-text")).to_contain_text(message)

    def expect_toast(self, message: str) -> None:
        expect(self.page.locator("#toast-message-span")).to_contain_text(message)

    def share_url(self) -> str:
        # Read off the copy button rather than the clipboard, which headless Chromium keeps
        # behind a permission prompt.
        return self.page.locator("[data-copy-share-url]").get_attribute("data-share-url")
