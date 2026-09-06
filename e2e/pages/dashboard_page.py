from playwright.sync_api import expect

from e2e.pages.base_page import BasePage


class DashboardPage(BasePage):
    """The room list at core:welcome.

    Every locator is scoped to a class the dashboard alone uses. The side menu renders the same
    rooms before #base-content, under .room-entry and .room-name, so anything addressed by text
    or by "the first one" would match a menu row instead of a card.
    """

    def card_for(self, target_url: str):
        return self.page.locator(f'.room-overview-card[hx-get="{target_url}"]')

    def expect_room_order(self, names: list[str]):
        expect(self.page.locator(".room-overview-name")).to_have_text(names)

    def expect_amount(self, target_url: str, *, label: str, value: str):
        amount = self.card_for(target_url).locator(".room-overview-amount")
        expect(amount.locator(".room-overview-amount-label")).to_have_text(label)
        expect(amount.locator(".room-overview-amount-value")).to_have_text(value)

    def expect_settled(self, target_url: str):
        card = self.card_for(target_url)
        expect(card.locator(".room-overview-amount-value")).to_have_text("All settled")
        expect(card.locator(".room-overview-amount-label")).to_have_count(0)

    def expect_no_status_badge(self, target_url: str):
        expect(self.card_for(target_url).locator(".room-status-badge")).to_have_count(0)

    def expect_status_badge(self, target_url: str, label: str):
        expect(self.card_for(target_url).locator(".room-status-badge")).to_have_text(label)

    def expect_side_by_side(self, left_target_url: str, right_target_url: str):
        left = self.card_for(left_target_url).bounding_box()
        right = self.card_for(right_target_url).bounding_box()

        # A pixel of tolerance: the two cards sit in the same grid row, not on the same subpixel.
        assert abs(left["y"] - right["y"]) <= 1, "the two cards are not in the same row"
        assert left["x"] < right["x"]

    def expect_last_used(self, target_url: str, text: str):
        expect(self.card_for(target_url).locator(".room-overview-activity")).to_have_text(text)

    def expect_no_last_used(self, target_url: str):
        expect(self.card_for(target_url).locator(".room-overview-activity")).to_have_count(0)

    def expect_no_amount(self, target_url: str):
        expect(self.card_for(target_url).locator(".room-overview-amount")).to_have_count(0)

    def expect_section_is_collapsed(self, section_id: str):
        expect(self.page.locator(f"#{section_id}")).to_be_hidden()

    def expand_section(self, section_id: str):
        self.page.locator(f'.room-overview-toggle[aria-controls="{section_id}"]').click()
        expect(self.page.locator(f"#{section_id}")).to_be_visible()

    def expect_summary(self, *, owed: list[str], received: list[str]):
        expect(self.page.locator(".room-balance-tile.owing .room-balance-value")).to_have_text(owed)
        expect(self.page.locator(".room-balance-tile.receiving .room-balance-value")).to_have_text(received)

    def expect_no_summary(self):
        expect(self.page.locator(".room-balance-summary")).to_have_count(0)
