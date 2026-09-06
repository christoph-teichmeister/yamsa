from playwright.sync_api import expect

from e2e.pages.base_page import BasePage


class TransactionDetailPage(BasePage):
    """The breakdown of a single transaction, used here to read back what was filed."""

    def expect_category(self, category_name: str):
        expect(self.page.locator(".transaction-meta").first).to_contain_text(category_name)
