from e2e.pages.base_page import BasePage


class ForgotPasswordPage(BasePage):
    def request_link(self, email: str) -> None:
        self.page.fill("#id_email", email)
        self.page.get_by_role("button", name="Request a new password").click()
        self.page.wait_for_url(lambda url: self.path not in url)
