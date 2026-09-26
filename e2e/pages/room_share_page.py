from e2e.pages.base_page import BasePage


class RoomSharePage(BasePage):
    """What an anonymous visitor sees behind a room's share link."""

    def __init__(self, page, share_url: str):
        # The link is absolute, the way the app hands it out, so it carries its own host.
        super().__init__(page, base_url="", path=share_url)

    def claim_guest_seat(self, guest_name: str):
        self.page.locator("#userSelect").select_option(label=guest_name)
        self.page.get_by_role("button", name="That's me!").click()
