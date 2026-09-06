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
        # The radio itself is visually hidden by .btn-check, so the click has to go to its label.
        self.category_field.locator(f"label[data-category-slug='{category_slug}']").click()
