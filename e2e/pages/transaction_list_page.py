from playwright.sync_api import expect

from e2e.pages.base_page import BasePage


class TransactionListPage(BasePage):
    """The expense feed and its floating "Add transaction" pill.

    The pill is asserted through its computed opacity rather than through its state attribute
    alone: the attribute only means something once the utilities keyed off it have compiled.
    """

    @property
    def add_transaction_button(self):
        return self.page.locator("[data-hide-on-scroll]")

    @property
    def rows(self):
        return self.page.locator("#transaction-feed .transaction-row")

    def wait_for_feed(self):
        expect(self.rows.first).to_be_visible()

    def scroll_by(self, delta_y: int):
        self.page.mouse.wheel(0, delta_y)

    def scroll_until_row_count(self, expected_count: int, *, max_steps: int = 15, step: int = 300):
        """Scroll down in steps until the feed has loaded its next batch.

        One long scroll would land at the end of the page, where the pill is meant to come back
        no matter what the swap did — which is the opposite of what a batch-loading test needs.
        """
        for _ in range(max_steps):
            if self.rows.count() >= expected_count:
                break
            self.scroll_by(step)
            self.page.wait_for_timeout(200)

        expect(self.rows).to_have_count(expected_count)

    def expect_add_button_hidden(self):
        expect(self.add_transaction_button).to_have_attribute("data-scroll-hidden", "")
        expect(self.add_transaction_button).to_have_css("opacity", "0")

    def expect_add_button_visible(self):
        expect(self.add_transaction_button).not_to_have_attribute("data-scroll-hidden", "")
        expect(self.add_transaction_button).to_have_css("opacity", "1")
