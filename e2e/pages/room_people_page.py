from playwright.sync_api import expect

from e2e.pages.base_page import BasePage


class RoomPeoplePage(BasePage):
    """The room roster at account:list, and the guest form it leads to."""

    def add_guest(self, name: str):
        self.page.get_by_role("button", name="Add guest").click()
        self.page.locator("#id_name").fill(name)
        # The roster's own "Add guest" button is gone once the form has replaced it, so the name
        # now matches the form's submit button alone.
        with self.page.expect_response(lambda response: "/guest/create/" in response.url):
            self.page.get_by_role("button", name="Add guest").click()

    def expect_member(self, name: str):
        expect(self.page.locator("#body article").filter(has_text=name)).to_have_count(1)

    def share_url(self) -> str:
        # Read off the copy button rather than the clipboard, which headless Chromium keeps
        # behind a permission prompt.
        return self.page.locator("[data-copy-share-url]").get_attribute("data-share-url")
