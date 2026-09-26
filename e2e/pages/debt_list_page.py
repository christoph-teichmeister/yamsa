from playwright.sync_api import expect

from e2e.pages.base_page import BasePage


class DebtListPage(BasePage):
    """The optimised debt list and the confirmation a debtor settles through."""

    def row_for(self, debt_id: int):
        return self.page.locator(f'[data-debt-row="{debt_id}"]')

    def expect_row(self, debt_id: int, *, text: str, amount: str):
        row = self.row_for(debt_id)
        expect(row).to_contain_text(text)
        expect(row).to_contain_text(amount)

    def open_settle_confirmation(self, debt_id: int):
        self.row_for(debt_id).get_by_role("button", name="Mark as paid").click()
        expect(self.page.get_by_role("button", name="Yes, I paid this")).to_be_visible()

    def confirm_settlement(self):
        with self.page.expect_response(lambda response: "/settle/" in response.url):
            self.page.get_by_role("button", name="Yes, I paid this").click()

    def cancel_settlement(self):
        self.page.get_by_role("button", name="Cancel").click()

    def expect_settled(self, debt_id: int):
        row = self.row_for(debt_id)
        expect(row).to_contain_text("Settled on")
        expect(row.get_by_role("button", name="Mark as paid")).to_have_count(0)

    def expect_open_for_debtor(self, debt_id: int):
        expect(self.row_for(debt_id).get_by_role("button", name="Mark as paid")).to_be_visible()

    def expect_open_for_creditor(self, debt_id: int):
        row = self.row_for(debt_id)
        expect(row).to_contain_text("Open")
        expect(row.get_by_role("button", name="Mark as paid")).to_have_count(0)

    def expect_all_settled_badge(self):
        expect(self.page.locator("#body").get_by_text("All settled", exact=True)).to_be_visible()
