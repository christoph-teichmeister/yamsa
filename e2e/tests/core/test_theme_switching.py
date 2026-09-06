import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.account.tests.constants import DEFAULT_PASSWORD
from e2e.pages.login_page import LoginPage
from e2e.pages.side_menu_page import SideMenuPage


@pytest.mark.e2e
class TestThemeSwitching:
    @staticmethod
    def _menu(page, base_url, profile_user) -> SideMenuPage:
        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.navigate()
        login_page.login(profile_user.email, DEFAULT_PASSWORD)

        return SideMenuPage(page, base_url, reverse("core:welcome"))

    def test_the_theme_is_set_without_waiting_for_the_bundles(self, page, base_url, profile_user):
        # The document ships one default theme for every reader, so the theme has to be applied
        # from the inline head script. Cutting the deferred bundles is how this test tells the two
        # apart: if the attribute still follows the system here, no reader ever sees the other
        # theme flash by.
        menu = self._menu(page, base_url, profile_user)
        page.route("**/bundles/*.js", lambda route: route.abort())
        page.emulate_media(color_scheme="light")

        menu.navigate()

        expect(menu.html()).to_have_attribute("data-bs-theme", "light")

    def test_it_follows_the_system_until_a_theme_is_chosen(self, page, base_url, profile_user):
        menu = self._menu(page, base_url, profile_user)
        page.emulate_media(color_scheme="light")

        menu.navigate()

        expect(menu.html()).to_have_attribute("data-bs-theme", "light")

        page.emulate_media(color_scheme="dark")

        expect(menu.html()).to_have_attribute("data-bs-theme", "dark")

    def test_a_chosen_theme_survives_a_reload_and_ignores_the_system(self, page, base_url, profile_user):
        menu = self._menu(page, base_url, profile_user)
        page.emulate_media(color_scheme="light")
        menu.navigate()
        menu.open_menu()

        menu.choose_theme("dark")

        expect(menu.html()).to_have_attribute("data-bs-theme", "dark")

        page.reload()

        expect(menu.html()).to_have_attribute("data-bs-theme", "dark")

    def test_the_system_option_hands_the_theme_back(self, page, base_url, profile_user):
        menu = self._menu(page, base_url, profile_user)
        page.emulate_media(color_scheme="light")
        menu.navigate()
        menu.open_menu()
        menu.choose_theme("dark")
        expect(menu.html()).to_have_attribute("data-bs-theme", "dark")

        menu.choose_theme("auto")

        expect(menu.html()).to_have_attribute("data-bs-theme", "light")

        page.emulate_media(color_scheme="dark")

        expect(menu.html()).to_have_attribute("data-bs-theme", "dark")

    def test_the_chosen_preference_is_marked_on_its_button(self, page, base_url, profile_user):
        menu = self._menu(page, base_url, profile_user)
        page.emulate_media(color_scheme="light")
        menu.navigate()
        menu.open_menu()

        menu.choose_theme("dark")

        expect(menu.theme_button("dark")).to_have_attribute("aria-pressed", "true")
        expect(menu.theme_button("light")).to_have_attribute("aria-pressed", "false")
        # `auto` is a preference of its own: the system theme happens to be light here, but that
        # must not read as "light is selected".
        expect(menu.theme_button("auto")).to_have_attribute("aria-pressed", "false")
