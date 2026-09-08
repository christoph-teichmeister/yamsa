import pytest
from django.urls import reverse
from playwright.sync_api import expect

from apps.account.tests.constants import DEFAULT_PASSWORD
from e2e.pages.login_page import LoginPage

# Polls the cache rather than waiting for an event: warming runs on an idle callback in the worker,
# and nothing on the page reports when it is done.
PAGES_ARE_CACHED = """
async (paths) => {
  const names = await caches.keys();
  const pagesCache = names.find((name) => name.includes('-pages-'));
  if (!pagesCache) {
    return false;
  }
  const keys = await (await caches.open(pagesCache)).keys();
  const cached = keys.map((request) => new URL(request.url).pathname);
  return paths.every((path) => cached.includes(path));
}
"""

PAGES_ARE_NOT_CACHED = f"async (paths) => !(await ({PAGES_ARE_CACHED})(paths))"


# page.wait_for_function() polls its predicate synchronously and reads a returned Promise as
# truthy, so it cannot wait on anything that has to be awaited - and reading cache storage does.
# page.evaluate() does await, so the polling happens here instead.
def _wait_until(page, expression, arg, timeout_ms=10_000, interval_ms=100):
    for _ in range(timeout_ms // interval_ms):
        if page.evaluate(expression, arg):
            return
        page.wait_for_timeout(interval_ms)

    error_message = f"Condition never held within {timeout_ms}ms: {expression}"
    raise AssertionError(error_message)


@pytest.mark.e2e
class TestOffline:
    @staticmethod
    def _room_paths(room):
        return [
            reverse("transaction:list", kwargs={"room_slug": room.slug}),
            reverse("debt:list", kwargs={"room_slug": room.slug}),
            reverse("account:list", kwargs={"room_slug": room.slug}),
            reverse("room:detail", kwargs={"room_slug": room.slug}),
            # Warmed last. Waiting for it too is what keeps a test from racing the tail of the
            # warm-up with whatever it does next.
            reverse("transaction:create", kwargs={"room_slug": room.slug}),
        ]

    @staticmethod
    def _sign_in(page, base_url, profile_user):
        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.navigate()
        login_page.login(profile_user.email, DEFAULT_PASSWORD)

    @staticmethod
    def _go_offline(page):
        """Cut the connection for the worker too.

        page.context.set_offline() only reaches requests the page itself makes; a fetch the service
        worker issues goes around it and would still be answered, so the cache would never be the
        thing under test. Routing aborts both, and set_offline is what navigator.onLine reads.
        """
        page.context.route("**/*", lambda route: route.abort())
        page.context.set_offline(True)

    @staticmethod
    def _open_controlled(page, base_url, path):
        """Open a path and come back once a service worker is actually driving the page.

        The first navigation of a fresh profile installs the worker but is not yet controlled by
        it, so nothing about that load reaches the cache.
        """
        page.goto(f"{base_url}{path}")
        page.wait_for_function("() => navigator.serviceWorker.controller !== null")
        page.goto(f"{base_url}{path}")
        page.wait_for_load_state("load")

    def test_a_visited_room_page_is_readable_without_a_connection(self, page, base_url, profile_user, shared_room):
        paths = self._room_paths(shared_room)
        self._sign_in(page, base_url, profile_user)
        self._open_controlled(page, base_url, paths[0])
        _wait_until(page, PAGES_ARE_CACHED, paths)

        self._go_offline(page)
        page.reload()

        expect(page.locator("[data-offline-banner]")).to_be_visible()
        expect(page.locator("[data-offline-cached-at]")).not_to_be_empty()
        expect(page.locator("#base-content")).not_to_contain_text("You seem to be offline")

    def test_the_banner_shows_even_where_the_browser_claims_to_be_online(
        self, page, base_url, profile_user, shared_room
    ):
        """navigator.onLine answers "attached to a network", not "reaches the server".

        It is true on a device behind a captive portal, and CI's browser reports it true with the
        network cut out from under it - which is how the banner came to be missing there while
        every local run showed it.
        """
        page.add_init_script("Object.defineProperty(navigator, 'onLine', {get: () => true});")
        paths = self._room_paths(shared_room)
        self._sign_in(page, base_url, profile_user)
        self._open_controlled(page, base_url, paths[0])
        _wait_until(page, PAGES_ARE_CACHED, paths)

        self._go_offline(page)
        page.reload()

        expect(page.locator("[data-offline-banner]")).to_be_visible()

    def test_the_rooms_other_tabs_are_warmed_before_they_are_visited(self, page, base_url, profile_user, shared_room):
        """Only what was clicked would be readable otherwise, which is not something to promise."""
        paths = self._room_paths(shared_room)
        debts_path = paths[1]
        self._sign_in(page, base_url, profile_user)
        self._open_controlled(page, base_url, paths[0])
        _wait_until(page, PAGES_ARE_CACHED, paths)

        self._go_offline(page)
        page.goto(f"{base_url}{debts_path}")

        expect(page.locator("#base-content")).not_to_contain_text("You seem to be offline")
        expect(page.locator("[data-offline-banner]")).to_be_visible()

    def test_the_offline_page_does_not_take_the_cache_down_with_it(self, page, base_url, profile_user, shared_room):
        """It is precached without an account and then shown for any unreachable page.

        Letting it report that account would read as a sign-out, and one unreachable page would
        cost the visitor every page they had saved.
        """
        paths = self._room_paths(shared_room)
        self._sign_in(page, base_url, profile_user)
        self._open_controlled(page, base_url, paths[0])
        _wait_until(page, PAGES_ARE_CACHED, paths)

        self._go_offline(page)
        page.goto(f"{base_url}{reverse('core:welcome')}")
        expect(page.locator("#base-content")).to_contain_text("You seem to be offline")

        page.goto(f"{base_url}{paths[0]}")

        expect(page.locator("#base-content")).not_to_contain_text("You seem to be offline")

    def test_signing_out_takes_the_cached_pages_with_it(self, page, base_url, profile_user, shared_room):
        """Cache storage outlives the session, so the next person on this browser would read them."""
        paths = self._room_paths(shared_room)
        self._sign_in(page, base_url, profile_user)
        self._open_controlled(page, base_url, paths[0])
        _wait_until(page, PAGES_ARE_CACHED, paths)

        page.goto(f"{base_url}{reverse('account:logout')}")
        _wait_until(page, PAGES_ARE_NOT_CACHED, paths)

        self._go_offline(page)
        page.goto(f"{base_url}{paths[0]}")

        expect(page.locator("#base-content")).to_contain_text("You seem to be offline")
