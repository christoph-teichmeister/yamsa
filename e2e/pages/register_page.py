from e2e.pages.base_page import BasePage


class RegisterPage(BasePage):
    def register(self, *, name: str, email: str | None, password: str):
        self.page.locator("#name").fill(name)
        if email is not None:
            self.page.locator("#email").fill(email)
        self.page.locator("#password").fill(password)
        self.page.get_by_role("button", name="Register now").click()
