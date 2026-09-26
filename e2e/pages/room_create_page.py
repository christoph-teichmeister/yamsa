from e2e.pages.base_page import BasePage


class RoomCreatePage(BasePage):
    def fill(self, *, name: str, description: str, currency_label: str | None = None):
        self.page.locator("#name").fill(name)
        self.page.locator("#description").fill(description)
        if currency_label is not None:
            self.page.locator("#preferred_currency").select_option(label=currency_label)

    def submit(self):
        self.page.locator("#create-room-button").click()
