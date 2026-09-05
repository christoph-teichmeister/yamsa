import pytest
from django.urls import reverse

from apps.account.tests.constants import DEFAULT_PASSWORD
from e2e.pages.login_page import LoginPage


@pytest.mark.e2e
class TestLogin:
    def test_user_can_log_in(self, page, base_url, profile_user):
        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.navigate()
        login_page.login(profile_user.email, DEFAULT_PASSWORD)

        assert reverse("account:login") not in page.url

    def test_wrong_password_shows_an_error_instead_of_redirecting(self, page, base_url, profile_user):
        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.navigate()
        login_page.login(profile_user.email, "not-the-password", expect_redirect=False)

        login_page.expect_auth_failed_error_visible()
        assert reverse("account:login") in page.url
