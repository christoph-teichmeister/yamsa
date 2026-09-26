from playwright.sync_api import expect

from e2e.pages.base_page import BasePage


class TransactionDetailPage(BasePage):
    """The breakdown of a single transaction, used here to read back what was filed."""

    def expect_category(self, category_name: str):
        expect(self.page.locator(".transaction-meta").first).to_contain_text(category_name)

    @property
    def receipts_section(self):
        return self.page.locator("#transaction-receipts-section")

    def receipt_card(self, original_name: str):
        return self.receipts_section.locator("article").filter(has_text=original_name)

    def upload_receipt(self, *, name: str, mime_type: str, content: bytes):
        # The input is sr-only and submits on its own change event, so the file is set on it
        # directly instead of going through a file chooser.
        with self.page.expect_response(lambda response: "/receipt/upload/" in response.url):
            self.receipts_section.locator("input[type='file']").set_input_files(
                {"name": name, "mimeType": mime_type, "buffer": content}
            )

    def delete_receipt(self, original_name: str):
        # hx-confirm asks through the browser's own confirm(), which Playwright would dismiss.
        self.page.once("dialog", lambda dialog: dialog.accept())
        with self.page.expect_response(lambda response: "/receipt/delete/" in response.url):
            self.receipt_card(original_name).get_by_role("button", name="Delete receipt").click()

    def expect_receipt(self, original_name: str):
        expect(self.receipt_card(original_name)).to_be_visible()

    def expect_no_receipts(self):
        expect(self.receipts_section.locator("article")).to_have_count(0)
        expect(self.receipts_section).to_contain_text("No receipts have been attached to this transaction yet.")

    def expect_receipt_error(self, message: str):
        expect(self.receipts_section.locator(".text-danger-text")).to_contain_text(message)

    def expect_receipt_not_deletable(self, original_name: str):
        expect(self.receipt_card(original_name).get_by_role("button", name="Delete receipt")).to_have_count(0)

    def expect_upload_closed(self):
        expect(self.receipts_section.locator("input[type='file']")).to_have_count(0)
        expect(self.receipts_section).to_contain_text("Receipts cannot be uploaded after the room has been closed.")
