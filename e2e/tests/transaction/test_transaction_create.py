import pytest

from apps.transaction.models import Category
from apps.transaction.tests.factories import ParentTransactionFactory
from e2e.tests.transaction.conftest import ACTIVITIES, GROCERIES


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
