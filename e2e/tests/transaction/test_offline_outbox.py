import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.transaction.models import ParentTransaction
from e2e.pages.login_page import LoginPage
from e2e.pages.transaction_create_page import TransactionCreatePage
from e2e.tests.core.test_offline import PAGES_ARE_CACHED, _wait_until

OUTBOX_SIZE = """
async () => {
  const database = await new Promise((resolve, reject) => {
    const request = indexedDB.open('yamsa-outbox', 1);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
  try {
    return await new Promise((resolve, reject) => {
      const request = database.transaction('entries', 'readonly').objectStore('entries').getAll();
      request.onsuccess = () => resolve(request.result.length);
      request.onerror = () => reject(request.error);
    });
  } finally {
    database.close();
  }
}
"""

OUTBOX_IS_EMPTY = f"async () => (await ({OUTBOX_SIZE})()) === 0"
OUTBOX_HOLDS_ONE = f"async () => (await ({OUTBOX_SIZE})()) === 1"


@pytest.mark.e2e
class TestOfflineOutbox:
    @staticmethod
    def _room_paths(room):
        return [
            reverse("transaction:list", kwargs={"room_slug": room.slug}),
            reverse("debt:list", kwargs={"room_slug": room.slug}),
            reverse("account:list", kwargs={"room_slug": room.slug}),
            reverse("room:detail", kwargs={"room_slug": room.slug}),
            reverse("transaction:create", kwargs={"room_slug": room.slug}),
        ]

    def _prepare(self, page, base_url, profile_user, room):
        """Sign in and let the worker take over and warm the room.

        Uses the transaction suite's own room fixture: these tests run against a transactional
        database, which flushes the categories the migration seeded, and the form has no chips to
        pick from without them.
        """
        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.navigate()
        login_page.login(profile_user.email, DEFAULT_PASSWORD)

        paths = self._room_paths(room)
        page.goto(f"{base_url}{paths[0]}")
        page.wait_for_function("() => navigator.serviceWorker.controller !== null")
        page.goto(f"{base_url}{paths[0]}")
        _wait_until(page, PAGES_ARE_CACHED, paths)
        return paths

    @staticmethod
    def _go_offline(page):
        page.context.route("**/*", lambda route: route.abort())
        page.context.set_offline(True)

    @staticmethod
    def _go_online(page):
        page.context.unroute("**/*")
        page.context.set_offline(False)

    @staticmethod
    def _add_expense_offline(page, base_url, room, description):
        create_page = TransactionCreatePage(
            page, base_url, reverse("transaction:create", kwargs={"room_slug": room.slug})
        )
        create_page.navigate()
        create_page.fill_required_fields(description=description, amount="12.50")
        create_page.choose_category("groceries")
        create_page.submit()
        return create_page

    def test_an_expense_entered_offline_is_kept_and_shown_as_waiting(self, page, base_url, profile_user, room):
        paths = self._prepare(page, base_url, profile_user, room)
        self._go_offline(page)
        page.goto(f"{base_url}{reverse('transaction:create', kwargs={'room_slug': room.slug})}")

        self._add_expense_offline(page, base_url, room, "Bought bread offline")

        _wait_until(page, OUTBOX_HOLDS_ONE, None)
        # The form hands over to the list, which offline comes out of the cache.
        expect(page).to_have_url(f"{base_url}{paths[0]}")
        expect(page.locator("[data-outbox-pending]")).to_be_visible()
        expect(page.locator("[data-outbox-pending]")).to_contain_text("Bought bread offline")
        assert not ParentTransaction.objects.filter(description="Bought bread offline").exists()

    def test_the_queue_drains_once_the_connection_is_back(self, page, base_url, profile_user, room):
        self._prepare(page, base_url, profile_user, room)
        self._go_offline(page)
        page.goto(f"{base_url}{reverse('transaction:create', kwargs={'room_slug': room.slug})}")
        self._add_expense_offline(page, base_url, room, "Bought milk offline")
        _wait_until(page, OUTBOX_HOLDS_ONE, None)

        self._go_online(page)
        page.evaluate("() => navigator.serviceWorker.controller.postMessage({type: 'yamsa:replay'})")
        _wait_until(page, OUTBOX_IS_EMPTY, None)

        booked = ParentTransaction.objects.filter(description="Bought milk offline")
        assert booked.count() == 1
        assert booked.first().child_transactions.count() == room.users.count()

    def test_two_expenses_entered_offline_are_both_booked(self, page, base_url, profile_user, room):
        """Both come from the same cached form, which was rendered with one submission name.

        Left as rendered, the second would reach the server looking like a replay of the first and
        be folded away - the visitor would lose an expense and never be told.
        """
        create_path = reverse("transaction:create", kwargs={"room_slug": room.slug})
        self._prepare(page, base_url, profile_user, room)
        self._go_offline(page)

        page.goto(f"{base_url}{create_path}")
        self._add_expense_offline(page, base_url, room, "First offline expense")
        _wait_until(page, OUTBOX_HOLDS_ONE, None)

        page.goto(f"{base_url}{create_path}")
        self._add_expense_offline(page, base_url, room, "Second offline expense")
        _wait_until(page, f"async () => (await ({OUTBOX_SIZE})()) === 2", None)

        self._go_online(page)
        page.evaluate("() => navigator.serviceWorker.controller.postMessage({type: 'yamsa:replay'})")
        _wait_until(page, OUTBOX_IS_EMPTY, None)

        assert ParentTransaction.objects.filter(description="First offline expense").count() == 1
        assert ParentTransaction.objects.filter(description="Second offline expense").count() == 1

    def test_replaying_twice_books_the_expense_once(self, page, base_url, profile_user, room):
        """The queue is drained by whatever gets there first; both must be safe."""
        self._prepare(page, base_url, profile_user, room)
        self._go_offline(page)
        page.goto(f"{base_url}{reverse('transaction:create', kwargs={'room_slug': room.slug})}")
        self._add_expense_offline(page, base_url, room, "Bought jam offline")
        _wait_until(page, OUTBOX_HOLDS_ONE, None)

        self._go_online(page)
        page.evaluate("() => navigator.serviceWorker.controller.postMessage({type: 'yamsa:replay'})")
        _wait_until(page, OUTBOX_IS_EMPTY, None)
        page.evaluate("() => navigator.serviceWorker.controller.postMessage({type: 'yamsa:replay'})")
        page.wait_for_timeout(1000)

        assert ParentTransaction.objects.filter(description="Bought jam offline").count() == 1
