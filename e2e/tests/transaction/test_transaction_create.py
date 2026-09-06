import pytest
from django.urls import reverse

from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.room.tests.factories import RoomFactory
from apps.transaction.models import Category, RoomCategory
from apps.transaction.tests.factories import ParentTransactionFactory
from e2e.pages.login_page import LoginPage
from e2e.pages.transaction_create_page import TransactionCreatePage

GROCERIES = "groceries"
ACTIVITIES = "activities"
RESTAURANTS = "restaurants-and-bars"

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
def open_create_form(page, base_url, profile_user, room):
    def _open() -> TransactionCreatePage:
        login_page = LoginPage(page, base_url, reverse("account:login"))
        login_page.navigate()
        login_page.login(profile_user.email, DEFAULT_PASSWORD)

        create_page = TransactionCreatePage(
            page, base_url, reverse("transaction:create", kwargs={"room_slug": room.slug})
        )
        create_page.navigate()
        return create_page

    return _open


@pytest.mark.e2e
class TestTransactionCreateCategory:
    def test_categories_are_visible_without_opening_anything(self, open_create_form):
        create_page = open_create_form()

        create_page.expect_categories_visible()
        create_page.expect_no_category_selected()
        create_page.expect_suggestion_hint_visible(visible=False)

    def test_description_suggests_a_category(self, open_create_form):
        create_page = open_create_form()

        create_page.type_description("Rewe Einkauf")

        create_page.expect_selected_category(GROCERIES)
        create_page.expect_suggestion_hint_visible(visible=True)

    def test_a_suggestion_is_withdrawn_when_the_description_stops_matching(self, open_create_form):
        create_page = open_create_form()

        create_page.type_description("Rewe Einkauf")
        create_page.expect_selected_category(GROCERIES)

        create_page.type_description("Baecker um die Ecke")

        create_page.expect_no_category_selected()
        create_page.expect_suggestion_hint_visible(visible=False)

    def test_a_picked_category_survives_further_typing(self, open_create_form):
        create_page = open_create_form()

        create_page.type_description("Rewe Einkauf")
        create_page.expect_selected_category(GROCERIES)

        create_page.choose_category(ACTIVITIES)
        create_page.type_description("Rewe Einkauf am Samstag")

        create_page.expect_selected_category(ACTIVITIES)
        create_page.expect_suggestion_hint_visible(visible=False)

    def test_the_rooms_own_history_beats_the_static_keyword(self, open_create_form, room, profile_user):
        activities = Category.objects.get(slug=ACTIVITIES)
        for _ in range(2):
            ParentTransactionFactory(
                room=room,
                paid_by=profile_user,
                currency=room.preferred_currency,
                description="Pizza night",
                category=activities,
            )

        create_page = open_create_form()
        create_page.type_description("Pizza")

        create_page.expect_selected_category(ACTIVITIES)
