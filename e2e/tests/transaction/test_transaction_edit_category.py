import pytest
from django.db import connection
from django.urls import reverse

from apps.transaction.models import Category, ChildTransaction, ParentTransaction
from apps.transaction.tests.factories import ParentTransactionFactory
from e2e.pages.transaction_create_page import TransactionCreatePage
from e2e.pages.transaction_detail_page import TransactionDetailPage
from e2e.tests.transaction.conftest import ACTIVITIES, GROCERIES


@pytest.fixture
def parent_transaction(room, profile_user):
    parent_transaction = ParentTransactionFactory(
        room=room,
        paid_by=profile_user,
        currency=room.preferred_currency,
        description="Wocheneinkauf",
        category=Category.objects.get(slug=GROCERIES),
    )
    ChildTransaction.objects.create(
        parent_transaction=parent_transaction,
        paid_for=profile_user,
        value="20.00",
    )
    # live_server writes from its own thread, and on SQLite this test's connection would keep the
    # rows above locked against the UPDATE the edit form issues.
    connection.close()
    return parent_transaction


@pytest.mark.e2e
class TestTransactionEditCategory:
    def test_the_edit_form_starts_from_the_current_category(self, page, base_url, room, parent_transaction, logged_in):
        edit_page = self._open_edit_form(page, base_url, room, parent_transaction, logged_in)

        edit_page.expect_selected_category(GROCERIES)

    def test_the_category_can_be_changed(self, page, base_url, room, parent_transaction, logged_in):
        edit_page = self._open_edit_form(page, base_url, room, parent_transaction, logged_in)

        detail_path = reverse("transaction:detail", kwargs={"room_slug": room.slug, "pk": parent_transaction.id})

        edit_page.choose_category(ACTIVITIES)
        page.get_by_role("button", name="Save changes").click()

        # Saving redirects to the detail page; reading the DB before that lands would race the
        # request still in flight.
        page.wait_for_url(lambda url: url.endswith(detail_path))
        TransactionDetailPage(page, base_url, detail_path).expect_category("Activities")

        assert ParentTransaction.objects.get(pk=parent_transaction.pk).category.slug == ACTIVITIES

    @staticmethod
    def _open_edit_form(page, base_url, room, parent_transaction, logged_in) -> TransactionCreatePage:
        logged_in()
        # The edit form renders the very same category partial, so it is driven by the same object.
        edit_page = TransactionCreatePage(
            page,
            base_url,
            reverse("transaction:edit", kwargs={"room_slug": room.slug, "pk": parent_transaction.id}),
        )
        edit_page.navigate()
        return edit_page
