import re

from playwright.sync_api import expect

from e2e.pages.base_page import BasePage


class RoomDetailPage(BasePage):
    """The room, editable wherever it is shown.

    There is no edit mode: the action row after the fields is disabled until something differs
    from what was rendered, so the assertions below read that row rather than a mode.
    """

    def discard(self):
        self.page.locator("#discard-room-button").click()

    def save(self):
        with self.page.expect_response(lambda response: "/edit" in response.url):
            self.page.locator("#save-room-button").click()
        self.expect_actions_disabled()

    def expect_actions_disabled(self):
        expect(self.page.locator("#save-room-button")).to_be_disabled()
        expect(self.page.locator("#discard-room-button")).to_be_disabled()

    def expect_actions_enabled(self):
        expect(self.page.locator("#save-room-button")).to_be_enabled()
        expect(self.page.locator("#discard-room-button")).to_be_enabled()

    def mark_sheet(self, marker: str):
        """Tag the sheet so a later read proves whether it survived or was replaced."""

        self.page.locator("#room-sheet").evaluate("(sheet, value) => (sheet.dataset.e2eMarker = value)", marker)

    def read_sheet_marker(self) -> str | None:
        return self.page.locator("#room-sheet").evaluate("(sheet) => sheet.dataset.e2eMarker || null")

    def fill_name(self, name: str):
        self.page.locator("#name").fill(name)

    def fill_description(self, description: str):
        self.page.locator("#description").fill(description)

    def expect_name(self, name: str):
        expect(self.page.locator("#name")).to_have_value(name)

    def expect_heading(self, name: str):
        expect(self.page.locator("#room-name")).to_have_text(name)

    def expect_fields_editable(self):
        expect(self.page.locator("#name")).to_be_editable()
        expect(self.page.locator("#preferred_currency")).to_be_enabled()

    def expect_fields_inert(self):
        expect(self.page.locator("#name")).to_be_disabled()
        expect(self.page.locator("#preferred_currency")).to_be_disabled()

    def expect_status(self, label: str):
        expect(self.page.locator("#room-status-label")).to_have_text(label)

    def close_room(self):
        with self.page.expect_response(lambda response: "/status" in response.url):
            self.page.locator("#close-room-button").click()

    def reopen_room(self):
        with self.page.expect_response(lambda response: "/status" in response.url):
            self.page.locator("#reopen-room-button").click()

    def open_force_close_dialog(self):
        self.page.locator("#close-room-button").click()
        # The dialog has to be in the top layer, not merely carry the open attribute, or the
        # backdrop and Escape are dead.
        expect(self.page.locator("#force-close-dialog")).to_be_visible()

    def force_close_dialog_is_modal(self) -> bool:
        return self.page.evaluate("document.querySelector('#force-close-dialog').matches(':modal')")

    def dismiss_force_close_dialog(self):
        self.page.locator("#force-close-dialog [data-dialog-close]").last.click()
        expect(self.page.locator("#force-close-dialog")).not_to_be_visible()

    def confirm_force_close(self):
        with self.page.expect_response(lambda response: "/status" in response.url):
            self.page.locator("#force-close-confirm-button").click()

    def expect_actions_present(self):
        expect(self.page.locator("#save-room-button")).to_have_count(1)

    def expect_actions_absent(self):
        expect(self.page.locator("#save-room-button")).to_have_count(0)

    def expect_url_is_the_room(self):
        expect(self.page).to_have_url(re.compile(r"/detail$"))
