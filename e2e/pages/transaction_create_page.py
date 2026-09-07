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
        self.page.locator("#value").fill(amount)

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
