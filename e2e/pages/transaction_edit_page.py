from playwright.sync_api import expect

from e2e.pages.transaction_create_page import TransactionCreatePage


class TransactionEditPage(TransactionCreatePage):
    """The transaction edit form.

    It renders the same category partial and `.split-row` markup as the create form, so reading
    and filling shares is inherited. What differs is that a saved share is removed on the server
    right away, and that the whole transaction can be deleted from here.
    """

    def set_paid_by(self, participant: str):
        self.page.locator("#paid_by_select").select_option(label=participant)

    def add_participant(self, participant: str, amount: str):
        super().add_participant(participant)
        self.page.locator(".split-row").last.locator("input[name='value']").fill(amount)

    def save(self):
        self.page.get_by_role("button", name="Save changes").click()

    def remove_saved_share(self, participant: str, *, confirm: bool = True):
        # hx-confirm asks through the browser's own confirm(), which Playwright would dismiss.
        self.page.once("dialog", lambda dialog: dialog.accept() if confirm else dialog.dismiss())
        if not confirm:
            self._row_for(participant).get_by_role("button", name="Remove this share").click()
            return
        with self.page.expect_response(lambda response: "/child-transaction/delete/" in response.url):
            self._row_for(participant).get_by_role("button", name="Remove this share").click()

    @property
    def delete_button(self):
        return self.page.get_by_role("button", name="Delete", exact=True)

    def delete_transaction(self, *, confirm: bool = True):
        self.page.once("dialog", lambda dialog: dialog.accept() if confirm else dialog.dismiss())
        if not confirm:
            self.delete_button.click()
            return
        with self.page.expect_response(lambda response: "/parent-transaction/delete/" in response.url):
            self.delete_button.click()

    def expect_shares_locked(self, *, locked: bool):
        values = self.page.locator(".split-row input[name='value']")
        for index in range(values.count()):
            if locked:
                expect(values.nth(index)).not_to_be_editable()
            else:
                expect(values.nth(index)).to_be_editable()
        lock_hint = self.page.locator("#split-lock-hint")
        if locked:
            expect(lock_hint).to_be_visible()
        else:
            expect(lock_hint).to_be_hidden()
