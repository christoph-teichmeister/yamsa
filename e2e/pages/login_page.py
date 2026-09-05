from playwright.sync_api import expect

from e2e.pages.base_page import BasePage


class LoginPage(BasePage):
    def fill_credentials(self, email: str, password: str):
        self.page.fill("#id_email", email)
        self.page.fill("#id_password", password)

    def submit(self):
        with self.page.expect_response(lambda response: self.path in response.url):
            self.page.click("#login-submit-button")

    def login(self, email: str, password: str):
        self.fill_credentials(email, password)
        self.submit()
        # The login POST answers with a redirect. expect_response() returns on that response,
        # while the browser is still on the login URL and the redirect is in flight - a page.goto()
        # issued right after can then be superseded by it and land somewhere else entirely.
        self.page.wait_for_url(lambda url: self.path not in url)

    def expect_auth_failed_error_visible(self):
        expect(self.page.locator(".alert-danger")).to_be_visible()
