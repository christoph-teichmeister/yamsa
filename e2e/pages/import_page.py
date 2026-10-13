import re

from playwright.sync_api import Locator, expect

from e2e.pages.base_page import BasePage


class ImportPage(BasePage):
    """The two import steps: uploading an export file and checking what it will create.

    People and categories are addressed by their name in the file, which is what each row's
    accessible label carries, so a test never depends on the order the parser lists them in.
    """

    def upload(self, *, name: str, content: bytes, source: str | None = None) -> None:
        if source is not None:
            self.page.get_by_label("Source").select_option(source)
        self.page.get_by_label("Export file").set_input_files({"name": name, "mimeType": "text/csv", "buffer": content})
        self.page.get_by_role("button", name="Read file").click()

    def expect_upload_error(self, message: str) -> None:
        expect(self.page.locator("form").get_by_text(message)).to_be_visible()

    def expect_preview(self) -> None:
        expect(self.page.get_by_role("heading", name="Check the import")).to_be_visible()

    def person_assignment(self, column: str) -> Locator:
        return self.page.get_by_label(f"Assignment for {column}", exact=True)

    def assign_person(self, column: str, value: str) -> None:
        self.person_assignment(column).select_option(value)

    def assign_person_to(self, column: str, user_name: str) -> None:
        self.person_assignment(column).select_option(label=user_name)

    def name_guest(self, column: str, name: str) -> None:
        self.page.get_by_label(f"Guest name for {column}", exact=True).fill(name)

    def category_assignment(self, label: str) -> Locator:
        return self.page.get_by_label(f"Target category for {label}", exact=True)

    def create_category(self, label: str, *, name: str, emoji: str) -> None:
        self.category_assignment(label).select_option("new")
        self.page.get_by_label(f"New category name for {label}", exact=True).fill(name)
        self.page.get_by_label(f"Emoji for {label}", exact=True).fill(emoji)

    def set_room_name(self, name: str) -> None:
        self.page.get_by_label("Room name").fill(name)

    def summary_value(self, heading: str) -> Locator:
        """The figure on one tile of the "What will be imported" summary."""
        # Anchored: "Skipped rows" also heads the list of skipped rows below the summary.
        tile_heading = self.page.locator("p").filter(has_text=re.compile(rf"^\s*{re.escape(heading)}\s*$")).first
        return tile_heading.locator("xpath=following-sibling::p[1]")

    def confirm(self) -> None:
        self.page.get_by_role("button", name="Import now").click()

    def expect_toast(self, message: str) -> None:
        expect(self.page.locator("#toast-message-span")).to_contain_text(message)
