import os
from urllib.parse import urlparse

import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse

# Needed before the factory imports below (they touch the ORM at import time from Playwright's
# sync context). Cleared in pytest_unconfigure() below so it doesn't leak into other tests sharing
# this worker process.
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from apps.account.models import User
from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.account.tests.factories import GuestUserFactory, SuperuserFactory, UserFactory
from apps.room.tests.factories import RoomFactory
from e2e.pages.account_detail_page import AccountDetailPage
from e2e.pages.account_security_page import AccountSecurityPage
from e2e.pages.change_password_page import ChangePasswordPage
from e2e.pages.login_page import LoginPage
from e2e.pages.room_detail_page import RoomDetailPage


def pytest_unconfigure(config):
    os.environ.pop("DJANGO_ALLOW_ASYNC_UNSAFE", None)


@pytest.fixture(scope="session")
def base_url(live_server):
    return live_server.url


@pytest.fixture
def user_password():
    return DEFAULT_PASSWORD


@pytest.fixture(autouse=True)
def _fail_on_htmx_console_errors(page):
    # live_server writes to a real (transactional) DB and serves over real HTTP, so a broken
    # htmx request shows up as a browser console error rather than a Python exception — catch it
    # here instead of every test silently passing on a swap that never happened.
    htmx_errors = []

    def _on_console(message):
        if message.type == "error" and message.text.startswith("htmx:"):
            htmx_errors.append(message.text)

    page.on("console", _on_console)

    yield

    assert not htmx_errors, f"HTMX reported error(s) in the browser console: {htmx_errors}"


def _login(page, base_url, email: str, password: str):
    login_page = LoginPage(page, base_url, reverse("account:login"))
    login_page.navigate()
    login_page.login(email, password)
    return page


def _login_as_guest(page, base_url, guest: User):
    # Guest accounts get an unusable, non-hashed password on every save (see User.clean()) and can
    # never authenticate through the login form by design — the app only ever logs them in via
    # AuthenticateGuestUserView's direct login() call from a room invite link. Mirror that here by
    # seeding a real session server-side and handing the browser its cookie, instead of trying to
    # drive a login form the product intentionally has no path into for guests.
    client = Client()
    client.force_login(guest, backend="django.contrib.auth.backends.ModelBackend")
    session_cookie = client.cookies[settings.SESSION_COOKIE_NAME]
    page.context.add_cookies(
        [
            {
                "name": settings.SESSION_COOKIE_NAME,
                "value": session_cookie.value,
                "domain": urlparse(base_url).hostname,
                "path": "/",
            }
        ]
    )
    return page


@pytest.fixture
def profile_user(transactional_db):
    return UserFactory()


@pytest.fixture
def roommate(transactional_db):
    return UserFactory()


@pytest.fixture
def shared_room(profile_user, roommate):
    room = RoomFactory(created_by=profile_user)
    room.users.add(profile_user, roommate)
    return room


@pytest.fixture
def unrelated_user(transactional_db):
    return UserFactory()


@pytest.fixture
def guest_user(transactional_db):
    return GuestUserFactory()


@pytest.fixture
def superuser(transactional_db):
    return SuperuserFactory()


@pytest.fixture
def profile_detail_path(profile_user):
    return reverse("account:detail", kwargs={"pk": profile_user.id})


@pytest.fixture
def logged_in_profile_detail_page(page, base_url, profile_detail_path, profile_user):
    _login(page, base_url, profile_user.email, DEFAULT_PASSWORD)

    detail_page = AccountDetailPage(page, base_url, profile_detail_path)
    detail_page.navigate()
    return detail_page


@pytest.fixture
def room_with_open_debt(shared_room, profile_user, roommate):
    from decimal import Decimal

    from apps.debt.models import Debt

    Debt.objects.create(
        room=shared_room,
        debitor=roommate,
        creditor=profile_user,
        value=Decimal("12.50"),
        currency=shared_room.preferred_currency,
    )
    return shared_room


@pytest.fixture
def logged_in_room_detail_page(page, base_url, profile_user, shared_room):
    _login(page, base_url, profile_user.email, DEFAULT_PASSWORD)

    detail_page = RoomDetailPage(page, base_url, reverse("room:detail", kwargs={"room_slug": shared_room.slug}))
    detail_page.navigate()
    return detail_page


@pytest.fixture
def logged_in_security_page(page, base_url, profile_user):
    _login(page, base_url, profile_user.email, DEFAULT_PASSWORD)

    security_page = AccountSecurityPage(page, base_url, reverse("account:security", kwargs={"pk": profile_user.id}))
    security_page.navigate()
    return security_page


@pytest.fixture
def logged_in_change_password_page(page, base_url, profile_user):
    _login(page, base_url, profile_user.email, DEFAULT_PASSWORD)

    password_page = ChangePasswordPage(
        page, base_url, reverse("account:change-password", kwargs={"pk": profile_user.id})
    )
    password_page.navigate()
    return password_page


@pytest.fixture
def logged_in_guest_detail_page(page, base_url, guest_user):
    _login_as_guest(page, base_url, guest_user)

    guest_detail_path = reverse("account:detail", kwargs={"pk": guest_user.id})
    detail_page = AccountDetailPage(page, base_url, guest_detail_path)
    detail_page.navigate()
    return detail_page
