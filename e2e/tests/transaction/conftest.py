import pytest
from django.urls import reverse

from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.room.tests.factories import RoomFactory
from apps.transaction.models import Category, RoomCategory
from e2e.pages.login_page import LoginPage
from e2e.pages.transaction_create_page import TransactionCreatePage

GROCERIES = "groceries"
RESTAURANTS = "restaurants-and-bars"
ACTIVITIES = "activities"

ROOM_CATALOG = (
    (GROCERIES, "Groceries", "🛒"),
    (RESTAURANTS, "Restaurants & Bars", "🍽️"),
    (ACTIVITIES, "Activities", "🎟️"),
)


@pytest.fixture
def room(profile_user, roommate):
    room = RoomFactory(created_by=profile_user)
    room.users.add(profile_user, roommate)

    # These tests run against a transactional database, which flushes the categories the
    # migration seeded. The catalog the assertions rely on is therefore built here.
    for order_index, (slug, name, emoji) in enumerate(ROOM_CATALOG):
        category, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "emoji": emoji, "order_index": order_index},
        )
        RoomCategory.objects.get_or_create(
            room=room,
            category=category,
            defaults={"order_index": order_index, "is_default": order_index == 0},
        )
    return room


@pytest.fixture
def logged_in(page, base_url, profile_user):
    def _login():
        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.navigate()
        login_page.login(profile_user.email, DEFAULT_PASSWORD)

    return _login


@pytest.fixture
def open_create_form(page, base_url, room, logged_in):
    def _open() -> TransactionCreatePage:
        logged_in()
        create_page = TransactionCreatePage(
            page, base_url, reverse("transaction:create", kwargs={"room_slug": room.slug})
        )
        create_page.navigate()
        return create_page

    return _open
