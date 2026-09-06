import re

import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
class TestSecuritySettings:
    def test_the_page_offers_passkey_registration_while_none_exists(self, logged_in_security_page):
        logged_in_security_page.expect_loaded()

        logged_in_security_page.expect_passkey_registration_offered()
        # The registration error is hidden by the hidden attribute, which passkey-register.js
        # clears — a utility class would leave it invisible however the script behaves.
        logged_in_security_page.expect_registration_error_hidden()

    def test_the_password_row_opens_the_form_and_back_returns_to_the_profile(self, logged_in_security_page):
        logged_in_security_page.open_change_password()
        logged_in_security_page.go_back_to_profile()

    def test_the_profile_reaches_the_security_settings(self, logged_in_profile_detail_page):
        detail_page = logged_in_profile_detail_page
        detail_page.expect_security_section_visible()

        detail_page.page.locator("#security-section button[hx-get*='security']").click()

        expect(detail_page.page).to_have_url(re.compile(r"/security/"))
        expect(detail_page.page.get_by_role("heading", name="Security settings")).to_be_visible()
