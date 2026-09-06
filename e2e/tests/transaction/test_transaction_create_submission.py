import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.transaction.models import ParentTransaction
from e2e.pages.transaction_detail_page import TransactionDetailPage
from e2e.tests.transaction.conftest import ACTIVITIES


@pytest.mark.e2e
class TestTransactionCreateSubmission:
    def test_a_transaction_is_filed_under_the_chosen_category(self, open_create_form, room, page, base_url):
        create_page = open_create_form()

        create_page.fill_required_fields(description="Kino am Freitag", amount="24.00")
        create_page.choose_category(ACTIVITIES)
        create_page.submit()

        page.wait_for_url(lambda url: url.endswith(reverse("transaction:list", kwargs={"room_slug": room.slug})))
        expect(page.locator(".transaction-row")).to_contain_text("Kino am Freitag")

        parent_transaction = ParentTransaction.objects.get(room=room, description="Kino am Freitag")
        detail_page = TransactionDetailPage(
            page,
            base_url,
            reverse("transaction:detail", kwargs={"room_slug": room.slug, "pk": parent_transaction.id}),
        )
        detail_page.navigate()
        detail_page.expect_category("Activities")

    def test_the_form_does_not_submit_without_a_category(self, open_create_form, room, page):
        create_page = open_create_form()

        create_page.fill_required_fields(description="Ohne Kategorie", amount="9.00")
        create_page.submit()

        create_page.expect_category_reported_as_missing()
        assert page.url.endswith(reverse("transaction:create", kwargs={"room_slug": room.slug}))
        assert not ParentTransaction.objects.filter(room=room, description="Ohne Kategorie").exists()

    def test_the_category_manager_opens_beside_the_form(self, open_create_form, room, page):
        create_page = open_create_form()
        create_page.fill_required_fields(description="Noch nicht gespeichert", amount="5.00")

        manager_page = create_page.open_category_manager()

        assert reverse("transaction:category-manager", kwargs={"room_slug": room.slug}) in manager_page.url
        # The form keeps what was typed, which is the whole point of not swapping #body.
        expect(page.locator("#description")).to_have_value("Noch nicht gespeichert")
