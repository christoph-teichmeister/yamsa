from collections.abc import Callable

import pytest
from playwright.sync_api import Page, expect

from e2e.tests.transaction.conftest import GROCERIES


@pytest.mark.e2e
class TestTransactionCreateInvalidFieldReveal:
    """A submit that fails the browser's own checks has to say why on the page.

    iOS Safari shows no validation bubble, so without this the submit button looks dead.
    """

    def test_a_missing_amount_is_focused_and_explained_until_it_is_filled(
        self, open_create_form: Callable, page: Page
    ) -> None:
        create_page = open_create_form()
        create_page.type_description("Ohne Betrag")
        create_page.choose_category(GROCERIES)

        create_page.submit()

        total_input = page.locator("#total_value_input")
        expect(total_input).to_be_focused()
        expect(total_input).to_have_attribute("aria-invalid", "true")
        message_id = total_input.get_attribute("aria-describedby")
        expect(page.locator(f"#{message_id}")).to_be_visible()
        expect(page.locator(f"#{message_id}")).not_to_be_empty()

        create_page.set_total("12.00")

        expect(total_input).not_to_have_attribute("aria-invalid", "true")
        expect(page.locator(f"#{message_id}")).to_have_count(0)

    def test_a_missing_category_is_explained_on_the_group(self, open_create_form: Callable, page: Page) -> None:
        create_page = open_create_form()
        create_page.fill_required_fields(description="Ohne Kategorie", amount="9.00")

        create_page.submit()

        message = create_page.category_field.locator("[data-invalid-field-message]")
        expect(message).to_be_visible()
        expect(create_page.radio_for(GROCERIES)).to_have_attribute("aria-invalid", "true")

        create_page.choose_category(GROCERIES)

        expect(message).to_have_count(0)
        expect(create_page.radio_for(GROCERIES)).not_to_have_attribute("aria-invalid", "true")

    def test_an_invalid_field_in_the_collapsed_details_is_opened_and_focused(
        self, open_create_form: Callable, page: Page
    ) -> None:
        create_page = open_create_form()
        create_page.fill_required_fields(description="Zu früh", amount="9.00")
        create_page.choose_category(GROCERIES)
        details = page.locator("details")
        expect(details).not_to_have_attribute("open", "")
        # Earlier than the field's min, set by script: the field is not reachable while collapsed.
        page.locator("#paid_at_input").evaluate("input => { input.value = '2010-01-01T12:00'; }")

        create_page.submit()

        expect(details).to_have_attribute("open", "")
        expect(page.locator("#paid_at_input")).to_be_focused()
        expect(page.locator("#paid_at_input")).to_have_attribute("aria-invalid", "true")
