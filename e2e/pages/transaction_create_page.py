from playwright.sync_api import expect

from e2e.pages.base_page import BasePage


class TransactionCreatePage(BasePage):
    """The transaction create form.

    Categories are addressed by their slug rather than by their label, so the assertions stay
    put when a name is translated or a room renames a category.
    """

    @property
    def description_input(self):
        return self.page.locator("#description")

    @property
    def category_field(self):
        return self.page.locator("[data-category-field]")

    @property
    def suggestion_hint(self):
        return self.category_field.locator("[data-category-suggestion-hint]")

    def radio_for(self, category_slug: str):
        return self.category_field.locator(f"input[data-category-slug='{category_slug}']")

    def expect_categories_visible(self):
        expect(self.category_field).to_be_visible()
        expect(self.category_field.locator("label[data-category-slug]").first).to_be_visible()

    def expect_no_category_selected(self):
        expect(self.category_field.locator("input[type='radio']:checked")).to_have_count(0)

    def expect_selected_category(self, category_slug: str):
        expect(self.radio_for(category_slug)).to_be_checked()

    def expect_suggestion_hint_visible(self, *, visible: bool):
        if visible:
            expect(self.suggestion_hint).to_be_visible()
        else:
            expect(self.suggestion_hint).to_be_hidden()

    def type_description(self, text: str):
        self.description_input.fill(text)

    def choose_category(self, category_slug: str):
        # The radio is stretched over the chip at opacity 0, so the click goes to the label.
        self.category_field.locator(f"label[data-category-slug='{category_slug}']").click()

    def fill_required_fields(self, *, description: str, amount: str):
        self.type_description(description)
        self.set_total(amount)

    def set_total(self, amount: str):
        self.page.locator("#total_value_input").fill(amount)

    def shares(self) -> dict[str, str]:
        """Each split row's amount, keyed by the participant it is for.

        By name rather than position: the rows follow the room's member order, which a test does
        not control.
        """
        return dict(
            self.page.locator(".split-row").evaluate_all(
                """rows => rows.map(row => [
                    row.querySelector("select[name='paid_for']").selectedOptions[0].text.trim(),
                    row.querySelector("input[name='value']").value,
                ])"""
            )
        )

    def expect_shares(self, expected: dict[str, str]):
        # Per row through expect() rather than one comparison of shares(): a removal rebalances
        # on the next tick, so the amounts may still be settling when this is called.
        expect(self.page.locator(".split-row")).to_have_count(len(expected))
        assert sorted(self.shares()) == sorted(expected)
        for participant, amount in expected.items():
            expect(self._row_for(participant).locator("input[name='value']")).to_have_value(amount)

    def _row_for(self, participant: str):
        names = list(self.shares())
        return self.page.locator(".split-row").nth(names.index(participant))

    def set_share(self, participant: str, amount: str):
        self._row_for(participant).locator("input[name='value']").fill(amount)

    def remove_share(self, participant: str):
        self._row_for(participant).get_by_role("button", name="Remove this share").click()

    def add_participant(self, participant: str):
        rows = self.page.locator(".split-row")
        row_count = rows.count()
        self.page.get_by_role("button", name="Add participant").click()
        expect(rows).to_have_count(row_count + 1)
        rows.last.locator("select[name='paid_for']").select_option(label=participant)

    def submit(self):
        self.page.get_by_role("button", name="Add transaction").click()

    def open_category_manager(self):
        with self.page.context.expect_page() as new_page:
            self.category_field.get_by_role("link", name="Manage categories").click()
        return new_page.value

    def expect_category_reported_as_missing(self):
        # No chip is checked, so the browser blocks the submit on the radio group's own
        # constraint rather than letting the request through.
        missing = self.radio_for_any().evaluate("radio => radio.validity.valueMissing")
        assert missing, "Expected the category radio group to report a missing value."

    def radio_for_any(self):
        return self.category_field.locator("input[type='radio']").first
