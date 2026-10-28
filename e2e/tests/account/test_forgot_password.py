import re

import pytest
from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from playwright.sync_api import Page

from apps.account.models import User
from apps.account.tests.constants import DEFAULT_PASSWORD
from e2e.pages.forgot_password_page import ForgotPasswordPage
from e2e.pages.login_page import LoginPage
from e2e.pages.reset_password_page import ResetPasswordPage

NEW_PASSWORD = "Brand-new-pw-93!"


def _reset_path_from_outbox() -> str:
    message = mail.outbox[-1]
    text = message.body + "".join(content for content, _ in getattr(message, "alternatives", []))
    return re.search(r"/account/reset-password/[^/\s\"'<]+/[^/\s\"'<]+/", text).group(0)


@pytest.mark.e2e
class TestForgotPassword:
    @pytest.fixture(autouse=True)
    def _clean_state(self) -> None:
        cache.clear()
        mail.outbox.clear()

    def test_the_reset_link_sets_a_new_password_that_logs_in(
        self, page: Page, base_url: str, profile_user: User
    ) -> None:
        old_hash = profile_user.password
        forgot_page = ForgotPasswordPage(page, base_url, reverse("account:forgot-password"))
        forgot_page.navigate()
        forgot_page.request_link(profile_user.email)

        profile_user.refresh_from_db()
        assert profile_user.password == old_hash, "asking for a link must not touch the password"
        assert len(mail.outbox) == 1

        reset_page = ResetPasswordPage(page, base_url, _reset_path_from_outbox())
        reset_page.navigate()
        reset_page.set_password(NEW_PASSWORD)
        page.wait_for_url(lambda url: reverse("account:login") in url)

        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.login(profile_user.email, NEW_PASSWORD)
        assert reverse("account:login") not in page.url

    def test_the_reset_link_works_only_once(self, page: Page, base_url: str, profile_user: User) -> None:
        forgot_page = ForgotPasswordPage(page, base_url, reverse("account:forgot-password"))
        forgot_page.navigate()
        forgot_page.request_link(profile_user.email)
        reset_path = _reset_path_from_outbox()

        reset_page = ResetPasswordPage(page, base_url, reset_path)
        reset_page.navigate()
        reset_page.set_password(NEW_PASSWORD)
        page.wait_for_url(lambda url: reverse("account:login") in url)

        reset_page.navigate()

        page.wait_for_url(lambda url: reverse("account:forgot-password") in url)

    def test_an_unknown_address_gets_the_same_answer_and_no_mail(self, page: Page, base_url: str) -> None:
        forgot_page = ForgotPasswordPage(page, base_url, reverse("account:forgot-password"))
        forgot_page.navigate()
        forgot_page.request_link("nobody@yamsa.local")

        assert reverse("account:login") in page.url
        assert not mail.outbox

    def test_the_old_password_still_works_until_the_link_is_used(
        self, page: Page, base_url: str, profile_user: User
    ) -> None:
        forgot_page = ForgotPasswordPage(page, base_url, reverse("account:forgot-password"))
        forgot_page.navigate()
        forgot_page.request_link(profile_user.email)

        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.navigate()
        login_page.login(profile_user.email, DEFAULT_PASSWORD)
        assert reverse("account:login") not in page.url
