import pytest

from apps.transaction.models import DEFAULT_CATEGORY_SLUG, Category, RoomCategory
from apps.transaction.services.room_category_service import RoomCategoryService

pytestmark = pytest.mark.django_db


class TestRoomCategoryService:
    def test_seeds_defaults_and_marks_default(self, room):
        service = RoomCategoryService(room=room)
        categories = list(service.get_categories())

        assert len(categories) == Category.objects.count()
        defaults = RoomCategory.objects.filter(room=room, is_default=True)
        assert defaults.count() == 1
        assert defaults.first().category.slug == DEFAULT_CATEGORY_SLUG

    def test_create_room_category_can_mark_default(self, room):
        service = RoomCategoryService(room=room)
        service.create_room_category(name="Private", emoji="🎯", color="#120A7D", make_default=True)

        default = RoomCategory.objects.get(room=room, is_default=True)
        assert default.category.slug.startswith("private")
        assert service.get_default_category().pk == default.category.pk

    def test_create_room_category_shifts_existing_categories(self, room):
        service = RoomCategoryService(room=room)
        initial_first = service.get_categories()[0]
        created = service.create_room_category(name="Room Tag", emoji="🚀", color="#FEDCBA", order_index=0)

        categories = list(service.get_categories())
        assert categories[0].id == created.id
        assert categories[1].category.slug == initial_first.category.slug
        assert [rc.order_index for rc in categories] == list(range(len(categories)))

    def test_update_room_category_reorders_without_changing_default(self, room):
        service = RoomCategoryService(room=room)
        categories_before = list(service.get_categories())
        target = categories_before[2]
        default_before = RoomCategory.objects.get(room=room, is_default=True)
        service.update_room_category(room_category_id=target.id, order_index=0, make_default=False)

        updated_categories = list(service.get_categories())
        assert updated_categories[0].id == target.id
        assert [rc.order_index for rc in updated_categories] == list(range(len(updated_categories)))
        assert RoomCategory.objects.get(room=room, is_default=True).id == default_before.id

    def test_delete_room_category_compacts_order(self, room):
        service = RoomCategoryService(room=room)
        categories = list(service.get_categories())
        target = categories[1]
        service.delete_room_category(target.id)

        remaining = list(service.get_categories())
        assert [rc.order_index for rc in remaining] == list(range(len(remaining)))

    def test_delete_default_promotes_next_category(self, room):
        service = RoomCategoryService(room=room)
        service.get_categories()
        default = RoomCategory.objects.get(room=room, is_default=True)
        service.delete_room_category(default.id)

        new_default = RoomCategory.objects.get(room=room, is_default=True)
        assert new_default.category.slug != default.category.slug
        assert service.get_default_category().slug == new_default.category.slug

    def test_category_queryset_includes_custom_room_category(self, room):
        service = RoomCategoryService(room=room)
        created = service.create_room_category(name="Room Private", emoji="🎨", color="#123456")

        queryset = list(service.get_category_queryset())
        assert any(category.pk == created.category.pk for category in queryset)
