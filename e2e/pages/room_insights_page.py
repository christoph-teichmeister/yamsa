from playwright.sync_api import expect

from e2e.pages.base_page import BasePage


class RoomInsightsPage(BasePage):
    """The two insight pages the debt list links to: "Who paid what" and the category breakdown."""

    def rows(self, kind: str) -> list[tuple[str, str]]:
        """Each (person, amount) row of one "Who paid what" list, in page order.

        `kind` is the list's data-insight-row value: "spent", "owed" or "covered".
        """
        return [
            tuple(cells)
            for cells in self.page.locator(f'[data-insight-row="{kind}"]').evaluate_all(
                # The name is the name cell's last element: the avatar before it may show an initial.
                """rows => rows.map(row => {
                    const [nameCell, amountCell] = row.querySelectorAll("p")
                    return [nameCell.lastElementChild.innerText.trim(), amountCell.innerText.trim()]
                })"""
            )
        ]

    def expect_rows(self, kind: str, expected: list[tuple[str, str]]):
        # Order-free: the lists sort by name only, so one person's rows in two currencies come in
        # no fixed order.
        expect(self.page.locator(f'[data-insight-row="{kind}"]')).to_have_count(len(expected))
        assert sorted(self.rows(kind)) == sorted(expected)

    def total_spent(self, currency_sign: str):
        heading = self.page.get_by_text(f"Total spent ({currency_sign})", exact=True)
        return heading.locator("xpath=following-sibling::p[1]")

    @property
    def trend(self):
        return self.page.locator("#spending-trend")

    def reveal_trend(self):
        # The timeline is only requested once it scrolls into view (hx-trigger="revealed once").
        self.trend.scroll_into_view_if_needed()
        expect(self.trend.get_by_text("Expense build-up")).to_be_visible()

    def trend_range(self, button_label: str):
        return self.trend.get_by_role("group", name="Spending trend ranges").get_by_role(
            "button", name=button_label, exact=True
        )

    def choose_trend_range(self, button_label: str):
        with self.page.expect_response(lambda response: "/money-spent/trend" in response.url):
            self.trend_range(button_label).click()

    def legend_items(self, currency_code: str) -> list[tuple[str, str]]:
        """Each (category, amount) entry of one currency's breakdown legend, in page order."""
        return [
            tuple(entry)
            for entry in self.legend(currency_code)
            .locator("[data-category-legend-item]")
            .evaluate_all(
                """items => items.map(item => [
                    item.querySelector("[data-category-name]").innerText.trim(),
                    item.querySelector("[data-category-amount]").innerText.trim(),
                ])"""
            )
        ]

    def legend_shares(self, currency_code: str) -> list[str]:
        return self.legend(currency_code).locator("[data-category-share]").all_inner_texts()

    def open_legend_entry(self, currency_code: str, category_slug: str):
        self.legend(currency_code).locator(f'[data-category-slug="{category_slug}"]').click()

    def legend(self, currency_code: str):
        return self.page.locator(f'[data-category-breakdown="{currency_code}"] [data-category-legend]')
