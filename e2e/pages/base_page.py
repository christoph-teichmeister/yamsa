from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page, base_url: str, path: str | None = None):
        self.page = page
        self.base_url = base_url
        self.path = path

    def navigate(self):
        self.page.goto(f"{self.base_url}{self.path}")
        self.page.wait_for_load_state("load")
