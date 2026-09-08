import pytest
from django.db import connection
from django.urls import reverse

from apps.transaction.constants import TRANSACTION_FEED_PAGE_SIZE
from apps.transaction.models import Category, ChildTransaction
from apps.transaction.tests.factories import ParentTransactionFactory
from e2e.pages.transaction_list_page import TransactionListPage
from e2e.tests.transaction.conftest import GROCERIES

# Narrow enough that the rows wrap the way a phone shows them, short enough that a handful of
# transactions already makes the page scroll. The pill is a phone affordance to begin with.
PHONE_VIEWPORT = {"width": 390, "height": 700}
# Under one feed batch, so the feed's "revealed" sentinel never loads a second one and moves the
# end of the page mid-assertion.
SINGLE_BATCH_COUNT = TRANSACTION_FEED_PAGE_SIZE - 2


def _create_transactions(room, paid_by, count: int):
    groceries = Category.objects.get(slug=GROCERIES)
    for index in range(count):
        parent_transaction = ParentTransactionFactory(
            room=room,
            paid_by=paid_by,
            currency=room.preferred_currency,
            description=f"Transaction {index}",
            category=groceries,
        )
        ChildTransaction.objects.create(
            parent_transaction=parent_transaction,
            paid_for=paid_by,
            value="20.00",
        )
    # live_server reads from its own thread, and on SQLite this test's connection would keep the
    # rows above locked against it.
    connection.close()
    return room


@pytest.fixture
def room_with_transactions(room, profile_user):
    return _create_transactions(room, profile_user, SINGLE_BATCH_COUNT)


@pytest.fixture
def room_with_two_feed_batches(room, profile_user):
    return _create_transactions(room, profile_user, TRANSACTION_FEED_PAGE_SIZE * 2)


@pytest.mark.e2e
class TestTransactionListAddButton:
    @staticmethod
    def _open_list(page, base_url, room, logged_in) -> TransactionListPage:
        page.set_viewport_size(PHONE_VIEWPORT)
        logged_in()
        list_page = TransactionListPage(page, base_url, reverse("transaction:list", kwargs={"room_slug": room.slug}))
        list_page.navigate()
        list_page.wait_for_feed()
        return list_page

    def test_it_starts_visible(self, page, base_url, room_with_transactions, logged_in):
        list_page = self._open_list(page, base_url, room_with_transactions, logged_in)

        list_page.expect_add_button_visible()

    def test_it_springs_back_into_place_when_it_returns(self, page, base_url, room_with_transactions, logged_in):
        list_page = self._open_list(page, base_url, room_with_transactions, logged_in)

        list_page.scroll_by(400)
        list_page.expect_add_button_hidden()

        list_page.scroll_by(-100)

        list_page.expect_add_button_springs_back()

    def test_scrolling_down_hides_it(self, page, base_url, room_with_transactions, logged_in):
        list_page = self._open_list(page, base_url, room_with_transactions, logged_in)

        list_page.scroll_by(200)

        list_page.expect_add_button_hidden()

    def test_scrolling_back_up_brings_it_back(self, page, base_url, room_with_transactions, logged_in):
        list_page = self._open_list(page, base_url, room_with_transactions, logged_in)

        list_page.scroll_by(400)
        list_page.expect_add_button_hidden()

        list_page.scroll_by(-100)

        list_page.expect_add_button_visible()

    def test_it_stays_visible_at_the_end_of_the_list(self, page, base_url, room_with_transactions, logged_in):
        # Arriving at the bottom is a downward scroll, so only the end-of-page rule can keep the
        # pill up — which is where a reader who has been through the whole list wants it.
        list_page = self._open_list(page, base_url, room_with_transactions, logged_in)

        list_page.scroll_by(5000)

        list_page.expect_add_button_visible()

    def test_loading_the_next_feed_batch_leaves_it_hidden(self, page, base_url, room_with_two_feed_batches, logged_in):
        # The next batch arrives as an htmx swap while the reader is scrolling down, and a swap
        # that does not carry the pill must not count as a fresh page.
        list_page = self._open_list(page, base_url, room_with_two_feed_batches, logged_in)

        list_page.scroll_until_row_count(TRANSACTION_FEED_PAGE_SIZE * 2)

        list_page.expect_add_button_hidden()

    def test_it_still_reacts_after_a_tab_switch_and_back(self, page, base_url, room_with_transactions, logged_in):
        # The tabs swap #body by morphing it, which both replaces the pill and can carry its
        # hidden state across — the listeners have to outlive that and the state has to be reset.
        list_page = self._open_list(page, base_url, room_with_transactions, logged_in)
        list_page.scroll_by(400)
        list_page.expect_add_button_hidden()

        # A morph swap leaves the old page in the DOM until the response lands, so both hops have
        # to be waited out on the pushed URL — anything read in between still belongs to the page
        # that is on its way out.
        page.locator("#debt-tab").click()
        page.wait_for_url(lambda url: not url.endswith(list_page.path))
        page.locator("#transaction-tab").click()
        page.wait_for_url(lambda url: url.endswith(list_page.path))
        list_page.wait_for_feed()

        list_page.expect_add_button_visible()

        list_page.scroll_by(400)

        list_page.expect_add_button_hidden()
