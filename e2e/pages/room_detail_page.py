import re

from playwright.sync_api import Locator, expect

from apps.room.room_seal import SEAL_ICON_LABELS
from e2e.pages.base_page import BasePage


class RoomDetailPage(BasePage):
    """The room, editable wherever it is shown.

    There is no edit mode: the action row after the fields is disabled until something differs
    from what was rendered, so the assertions below read that row rather than a mode.
    """

    def discard(self) -> None:
        self.page.locator("#discard-room-button").click()

    def save(self) -> None:
        with self.page.expect_response(lambda response: "/edit" in response.url):
            self.page.locator("#save-room-button").click()
        self.expect_actions_disabled()

    def expect_actions_disabled(self) -> None:
        expect(self.page.locator("#save-room-button")).to_be_disabled()
        expect(self.page.locator("#discard-room-button")).to_be_disabled()

    def expect_actions_enabled(self) -> None:
        expect(self.page.locator("#save-room-button")).to_be_enabled()
        expect(self.page.locator("#discard-room-button")).to_be_enabled()

    def mark_sheet(self, marker: str) -> None:
        """Tag the sheet so a later read proves whether it survived or was replaced."""
        self.page.locator("#room-sheet").evaluate("(sheet, value) => (sheet.dataset.e2eMarker = value)", marker)

    def read_sheet_marker(self) -> str | None:
        return self.page.locator("#room-sheet").evaluate("(sheet) => sheet.dataset.e2eMarker || null")

    def fill_name(self, name: str) -> None:
        self.page.locator("#name").fill(name)

    def fill_description(self, description: str) -> None:
        self.page.locator("#description").fill(description)

    def expect_name(self, name: str) -> None:
        expect(self.page.locator("#name")).to_have_value(name)

    def expect_heading(self, name: str) -> None:
        expect(self.page.locator("#room-name")).to_have_text(name)

    def expect_fields_editable(self) -> None:
        expect(self.page.locator("#name")).to_be_editable()
        expect(self.page.locator("#preferred_currency")).to_be_enabled()

    def expect_fields_inert(self) -> None:
        expect(self.page.locator("#name")).to_be_disabled()
        expect(self.page.locator("#preferred_currency")).to_be_disabled()

    def expect_status(self, label: str) -> None:
        expect(self.page.locator("#room-status-label")).to_have_text(label)

    def close_room(self) -> None:
        # The happy-path close now confirms first, same as force-close and delete already did.
        self.page.locator("#close-room-button").click()
        expect(self.page.locator("#close-room-dialog")).to_be_visible()
        with self.page.expect_response(lambda response: "/status" in response.url):
            self.page.locator("#close-room-confirm-button").click()

    def reopen_room(self) -> None:
        with self.page.expect_response(lambda response: "/status" in response.url):
            self.page.locator("#reopen-room-button").click()

    def open_force_close_dialog(self) -> None:
        self.page.locator("#close-room-button").click()
        # The dialog has to be in the top layer, not merely carry the open attribute, or the
        # backdrop and Escape are dead.
        expect(self.page.locator("#force-close-dialog")).to_be_visible()

    def force_close_dialog_is_modal(self) -> bool:
        return self.page.evaluate("document.querySelector('#force-close-dialog').matches(':modal')")

    def dismiss_force_close_dialog(self) -> None:
        self.page.locator("#force-close-dialog [data-dialog-close]").last.click()
        expect(self.page.locator("#force-close-dialog")).not_to_be_visible()

    def confirm_force_close(self) -> None:
        with self.page.expect_response(lambda response: "/status" in response.url):
            self.page.locator("#force-close-confirm-button").click()

    def delete_room(self) -> None:
        self.page.locator("#delete-room-button").click()
        expect(self.page.locator("#delete-room-dialog")).to_be_visible()
        with self.page.expect_response(lambda response: response.url.endswith("/delete")):
            self.page.locator("#delete-room-confirm-button").click()

    def expect_no_delete_option(self) -> None:
        expect(self.page.locator("#delete-room-button")).to_have_count(0)

    def expect_actions_present(self) -> None:
        expect(self.page.locator("#save-room-button")).to_have_count(1)

    def expect_actions_absent(self) -> None:
        expect(self.page.locator("#save-room-button")).to_have_count(0)

    def expect_url_is_the_room(self) -> None:
        expect(self.page).to_have_url(re.compile(r"/detail$"))

    @property
    def seal(self) -> Locator:
        """The seal in the sheet's header, inside the button that opens its dialog."""
        return self.page.locator("#room-sheet [data-dialog-open='room-seal-dialog'] .room-seal")

    @property
    def seal_dialog(self) -> Locator:
        return self.page.locator("#room-seal-dialog")

    def open_seal_dialog(self) -> None:
        self.page.get_by_role("button", name="Change room seal").click()
        expect(self.seal_dialog).to_be_visible()

    def seal_icon_button(self, icon_name: str) -> Locator:
        # By the label a screen reader announces, which is what the button is named by.
        return self.seal_dialog.get_by_role("button", name=str(SEAL_ICON_LABELS[icon_name]), exact=True)

    def pick_seal_icon(self, icon_name: str) -> None:
        with self.page.expect_response(lambda response: response.url.endswith("/seal/icon")):
            self.seal_icon_button(icon_name).click()

    def upload_seal_image(self, file_name: str, content: bytes, mime_type: str = "image/png") -> None:
        # The input posts itself through htmx on change, so the file is set on it directly.
        with self.page.expect_response(lambda response: response.url.endswith("/seal/image")):
            self.seal_dialog.locator("#room-seal-image-input").set_input_files(
                {"name": file_name, "mimeType": mime_type, "buffer": content}
            )

    def reset_seal(self) -> None:
        # hx-confirm asks through the browser's own confirm(), which Playwright would dismiss.
        self.page.once("dialog", lambda dialog: dialog.accept())
        with self.page.expect_response(lambda response: response.url.endswith("/seal/reset")):
            self.seal_dialog.get_by_role("button", name="Reset to default").click()

    def expect_seal_icon(self, icon_name: str) -> None:
        expect(self.seal.locator("img")).to_have_count(0)
        expect(self.seal.locator("svg use").first).to_have_attribute("href", re.compile(rf"#{re.escape(icon_name)}$"))

    def expect_seal_image(self) -> None:
        expect(self.seal.locator("img")).to_have_count(1)
