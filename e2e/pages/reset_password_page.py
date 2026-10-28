from e2e.pages.base_page import BasePage


class ResetPasswordPage(BasePage):
    def set_password(self, password: str) -> None:
        self.page.fill("#new_password1", password)
        self.page.fill("#new_password2", password)
        self.page.get_by_role("button", name="Save").click()
