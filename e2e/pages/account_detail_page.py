from playwright.sync_api import expect

from e2e.pages.base_page import BasePage


class AccountDetailPage(BasePage):
    """The profile page, which reads and edits in the same place.

    Entering edit mode is a pure client-side flip: there is no request to wait for, so the
    assertions below check the controls themselves rather than a navigation.
    """

    def enter_edit_mode(self):
        self.page.locator("#edit-profile-button").click()
        expect(self.page.locator("#save-profile-button")).to_be_visible()

    def cancel_edit_mode(self):
        self.page.locator("#cancel-profile-button").click()
        expect(self.page.locator("#edit-profile-button")).to_be_visible()

    def save(self):
        with self.page.expect_response(lambda response: "/update/" in response.url):
            self.page.locator("#save-profile-button").click()
        expect(self.page.locator("#edit-profile-button")).to_be_visible()

    def mark_sheet(self, marker: str):
        """Tag the sheet element so a later read proves whether it survived or was replaced."""

        self.page.locator("#profile-sheet").evaluate("(sheet, value) => (sheet.dataset.e2eMarker = value)", marker)

    def read_sheet_marker(self) -> str | None:
        return self.page.locator("#profile-sheet").evaluate("(sheet) => sheet.dataset.e2eMarker || null")

    def open_photo_dialog(self):
        self.page.locator("button[data-profile-photo-open]").click()
        expect(self.page.locator("[data-profile-photo-dialog]")).to_be_visible()

    def open_photo_dialog_via_badge(self):
        self.page.locator("span[data-profile-photo-open]").click()
        expect(self.page.locator("[data-profile-photo-dialog]")).to_be_visible()

    def expect_photo_hover_hint(self, *, visible: bool):
        """The camera overlay may only show while the avatar is hovered.

        to_have_css retries, which a plain read cannot: the overlay fades in over a transition.
        """

        expect(self.page.locator("#profile-photo button span[aria-hidden]")).to_have_css(
            "opacity", "1" if visible else "0"
        )

    def hover_photo(self):
        self.page.locator("#profile-photo").hover()

    def move_pointer_away(self):
        self.page.mouse.move(0, 0)

    def close_photo_dialog(self):
        self.page.locator("[data-profile-photo-close]").click()
        expect(self.page.locator("[data-profile-photo-dialog]")).not_to_be_visible()

    def expect_photo_dialog_offers(self, *, delete: bool):
        expect(self.page.locator("label[for='profile-picture-input']")).to_be_visible()
        matcher = expect(self.page.locator("[data-profile-photo-delete]"))
        matcher.to_be_visible() if delete else matcher.to_have_count(0)

    def upload_photo_from_dialog(self, file_name: str, content: bytes):
        with self.page.expect_response(lambda response: "/profile-picture/update/" in response.url):
            self.page.set_input_files(
                "#profile-picture-input",
                files=[{"name": file_name, "mimeType": "image/png", "buffer": content}],
            )

    def delete_photo_from_dialog(self):
        self.page.once("dialog", lambda confirmation: confirmation.accept())
        with self.page.expect_response(lambda response: "/profile-picture/delete/" in response.url):
            self.page.locator("[data-profile-photo-delete]").click()

    def expect_photo_present(self):
        expect(self.page.locator("[data-profile-photo-open] img")).to_be_visible()

    def expect_no_photo(self):
        expect(self.page.locator("[data-profile-photo-open] img")).to_have_count(0)

    def profile_section_offset(self) -> float:
        """Where the first settings row sits, to catch the sheet growing on a mode switch."""

        box = self.page.locator("#name").bounding_box()
        return box["y"]

    def fill_name(self, name: str):
        self.page.fill("#name", name)

    def fill_email(self, email: str):
        self.page.fill("#email", email)

    def choose_language(self, language_code: str):
        self.page.select_option("#id_language", language_code)

    def choose_wants_notifications(self, *, wants_notifications: bool):
        checkbox = self.page.locator("#wants_to_receive_webpush_notifications")
        if wants_notifications:
            checkbox.check()
        else:
            checkbox.uncheck()

    def expect_name(self, name: str):
        expect(self.page.locator("#profile-name")).to_have_text(name)
        expect(self.page.locator("#name")).to_have_value(name)

    def expect_email(self, email: str):
        expect(self.page.locator("#email")).to_have_value(email)

    def expect_member_name(self, name: str):
        """The name as shown on someone else's profile, which carries no editable fields."""

        expect(self.page.locator("#profile-name")).to_have_text(name)

    def expect_fields_locked(self):
        expect(self.page.locator("#name")).to_have_attribute("readonly", "")
        expect(self.page.locator("#id_language")).to_be_disabled()
        expect(self.page.locator("#save-profile-button")).to_be_hidden()

    def expect_fields_editable(self):
        expect(self.page.locator("#name")).not_to_have_attribute("readonly", "")
        expect(self.page.locator("#id_language")).to_be_enabled()
        expect(self.page.locator("#edit-profile-button")).to_be_hidden()

    def expect_edit_button_visible(self):
        expect(self.page.locator("#edit-profile-button")).to_be_visible()

    def expect_edit_button_hidden(self):
        expect(self.page.locator("#edit-profile-button")).to_have_count(0)

    def expect_security_section_visible(self):
        expect(self.page.locator("#security-section")).to_be_visible()

    def expect_security_section_hidden(self):
        expect(self.page.locator("#security-section")).to_have_count(0)

    def expect_guest_mode_banner_visible(self):
        expect(self.page.locator("#guest-mode-banner")).to_be_visible()

    def mark_body_shell(self):
        """Tag the loading spinner with a JS property, which only survives if the node itself does.

        An attribute would be a false negative: morphing keeps the element but syncs its attributes
        to the incoming markup, which carries no marker.
        """

        self.page.locator("#body-loading-spinner").evaluate("(element) => (element.e2eSurvivedSwap = true)")

    def body_shell_survived(self) -> bool:
        return self.page.locator("#body-loading-spinner").evaluate("(element) => element.e2eSurvivedSwap === true")

    def open_change_password_via_security_row(self):
        with self.page.expect_response(lambda response: "/change-password/" in response.url):
            self.page.locator("#security-section button[hx-get*='change-password']").click()

    def expect_notifications_radio_checked(self, *, wants_notifications: bool):
        checkbox = self.page.locator("#wants_to_receive_webpush_notifications")
        if wants_notifications:
            expect(checkbox).to_be_checked()
        else:
            expect(checkbox).not_to_be_checked()
