from playwright.sync_api import Locator

from e2e.pages.base_page import BasePage


class SideMenuPage(BasePage):
    """The side menu, which is where the theme is switched."""

    def open_menu(self):
        self.page.locator(".navbar-toggler").click()
        self.page.locator("#offcanvasNavbar.show").wait_for(state="visible")

    def theme_button(self, preference: str) -> Locator:
        return self.page.locator(f'[data-theme-value="{preference}"]')

    def choose_theme(self, preference: str):
        self.theme_button(preference).click()

    def html(self) -> Locator:
        return self.page.locator("html")
