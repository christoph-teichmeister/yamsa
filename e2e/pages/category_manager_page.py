from playwright.sync_api import expect

from e2e.pages.base_page import BasePage


class CategoryManagerPage(BasePage):
    """The room's category catalog: add, reorder, promote to default and remove.

    Categories are addressed by their name, which is what the page shows; every action swaps the
    list in place, so each one waits for the manager's response before the next locator runs.
    """

    @property
    def cards(self):
        return self.page.locator("#room-category-list [role='listitem']")

    def card_for(self, name: str):
        return self.cards.filter(has=self.page.get_by_text(name, exact=True))

    def _submit(self, button):
        # Every action posts back to the manager's own URL.
        with self.page.expect_response(
            lambda response: response.request.method == "POST" and response.url.endswith(self.path)
        ):
            button.click()

    def add_category(self, *, name: str, emoji: str):
        form = self.page.locator("#room-category-creation-form")
        form.locator("#category-name").fill(name)
        form.locator("#category-emoji").fill(emoji)
        self._submit(form.get_by_role("button", name="Add category"))

    def remove(self, name: str):
        self._submit(self.card_for(name).get_by_role("button", name="Remove"))

    def move_to(self, name: str, order_index: int):
        card = self.card_for(name)
        card.locator("input[name='order_index']").fill(str(order_index))
        self._submit(card.get_by_role("button", name="Save order for this category"))

    def make_default(self, name: str):
        card = self.card_for(name)
        card.get_by_role("switch", name="Default").check()
        self._submit(card.get_by_role("button", name="Save order for this category"))

    def expect_order(self, names: list[str]):
        expect(self.cards.locator("div.min-w-0 > p.font-semibold")).to_have_text(names)

    def expect_default(self, name: str):
        # The badge beside the name, not the "Default" label every card's switch carries.
        badged = self.cards.filter(has=self.page.locator("div.min-w-0 > span", has_text="Default"))
        expect(badged.locator("div.min-w-0 > p.font-semibold")).to_have_text([name])

    def expect_creation_error(self):
        expect(self.page.locator("#room-category-creation-form p.text-danger-text").first).to_be_visible()
