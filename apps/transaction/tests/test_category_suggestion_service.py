import pytest

from apps.transaction.models import Category
from apps.transaction.services.category_suggestion_service import (
    BASE_CATEGORY_KEYWORDS,
    CategorySuggestionService,
    normalize_keyword,
    tokenize,
)
from apps.transaction.services.room_category_service import RoomCategoryService
from apps.transaction.tests.factories import ParentTransactionFactory

pytestmark = pytest.mark.django_db


class TestCategorySuggestionService:
    def test_keywords_are_unique_across_categories(self):
        seen: dict[str, str] = {}
        for slug, keywords in BASE_CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                assert keyword not in seen, f"'{keyword}' maps to both '{seen.get(keyword)}' and '{slug}'"
                seen[keyword] = slug

    def test_normalize_keyword_folds_case_and_diacritics(self):
        assert normalize_keyword("Café") == "cafe"

    def test_tokenize_drops_short_and_numeric_tokens(self):
        assert tokenize("Pizza 12 at da Toni") == ["pizza", "toni"]

    def test_static_keywords_point_at_the_rooms_own_categories(self, room):
        index = CategorySuggestionService(room=room).build_index()

        groceries = Category.objects.get(slug="groceries")
        assert index["rewe"] == groceries.id

    def test_index_only_contains_categories_the_room_offers(self, room):
        service = RoomCategoryService(room=room)
        removed = next(
            room_category
            for room_category in service.get_categories()
            if room_category.category.slug == "restaurants-and-bars"
        )
        service.delete_room_category(removed.id)

        index = CategorySuggestionService(room=room).build_index()

        assert "pizza" not in index
        assert "rewe" in index

    def test_room_history_overrides_a_static_keyword(self, room, user):
        activities = Category.objects.get(slug="activities")
        for _ in range(2):
            ParentTransactionFactory(room=room, paid_by=user, description="Pizza night", category=activities)

        index = CategorySuggestionService(room=room).build_index()

        assert index["pizza"] == activities.id

    def test_ambiguous_history_keyword_is_skipped(self, room, user):
        activities = Category.objects.get(slug="activities")
        household = Category.objects.get(slug="household")
        ParentTransactionFactory(room=room, paid_by=user, description="Kaution zurueck", category=activities)
        ParentTransactionFactory(room=room, paid_by=user, description="Kaution zurueck", category=household)

        index = CategorySuggestionService(room=room).build_index()

        assert "kaution" not in index

    def test_history_of_another_room_is_ignored(self, room, closed_room, user):
        activities = Category.objects.get(slug="activities")
        ParentTransactionFactory(room=closed_room, paid_by=user, description="Pizza night", category=activities)

        index = CategorySuggestionService(room=room).build_index()

        assert index["pizza"] == Category.objects.get(slug="restaurants-and-bars").id
