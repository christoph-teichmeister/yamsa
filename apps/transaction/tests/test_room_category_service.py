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

    def test_update_room_category_changes_order_without_changing_default(self, room):
        service = RoomCategoryService(room=room)
        target = service.get_categories()[0]
        service.update_room_category(room_category_id=target.id, order_index=55, make_default=False)

        target.refresh_from_db()
        assert target.order_index == 55
        assert not target.is_default

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
