import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.transaction.models import Category, ParentTransaction
from apps.transaction.tests.factories import ParentTransactionFactory
from e2e.pages.category_manager_page import CategoryManagerPage
from e2e.pages.transaction_create_page import TransactionCreatePage
from e2e.tests.transaction.conftest import GROCERIES


@pytest.fixture
def open_category_manager(page, base_url, room, logged_in):
    def _open() -> CategoryManagerPage:
        logged_in()
        manager_page = CategoryManagerPage(
            page, base_url, reverse("transaction:category-manager", kwargs={"room_slug": room.slug})
        )
        manager_page.navigate()
        return manager_page

    return _open


@pytest.mark.e2e
class TestCategoryManager:
    def test_a_new_category_is_offered_on_the_transaction_form(self, open_category_manager, room, page, base_url):
        manager_page = open_category_manager()

        manager_page.add_category(name="Haustier", emoji="🐶")

        manager_page.expect_order(["Groceries", "Restaurants & Bars", "Activities", "Haustier"])
        create_page = TransactionCreatePage(
            page, base_url, reverse("transaction:create", kwargs={"room_slug": room.slug})
        )
        create_page.navigate()
        expect(
            create_page.category_field.locator("label[data-category-slug]").filter(has_text="Haustier")
        ).to_be_visible()

    def test_a_category_without_a_single_emoji_is_rejected(self, open_category_manager):
        manager_page = open_category_manager()

        manager_page.add_category(name="Ohne Emoji", emoji="abc")

        manager_page.expect_creation_error()
        manager_page.expect_order(["Groceries", "Restaurants & Bars", "Activities"])
        assert not Category.objects.filter(name="Ohne Emoji").exists()

    def test_a_category_can_be_moved_to_the_front(self, open_category_manager):
        manager_page = open_category_manager()

        manager_page.move_to("Activities", 0)

        manager_page.expect_order(["Activities", "Groceries", "Restaurants & Bars"])

    def test_another_category_can_become_the_default(self, open_category_manager):
        manager_page = open_category_manager()
        manager_page.expect_default("Groceries")

        manager_page.make_default("Activities")

        manager_page.expect_default("Activities")

    def test_removing_the_default_moves_its_transactions_to_the_next_one(
        self, open_category_manager, room, profile_user
    ):
        groceries = Category.objects.get(slug=GROCERIES)
        transaction = ParentTransactionFactory(
            room=room, paid_by=profile_user, currency=room.preferred_currency, category=groceries
        )
        manager_page = open_category_manager()

        manager_page.remove("Groceries")

        manager_page.expect_order(["Restaurants & Bars", "Activities"])
        manager_page.expect_default("Restaurants & Bars")
        transaction = ParentTransaction.objects.get(id=transaction.id)
        assert transaction.category.name == "Restaurants & Bars"
