from __future__ import annotations

from collections.abc import Iterable

from django.db import transaction
from django.utils.text import slugify

from apps.room.models import Room
from apps.transaction.models import DEFAULT_CATEGORY_SLUG, Category, RoomCategory


class RoomCategoryService:
    room: Room

    def __init__(self, room: Room):
        self.room = room

    def get_categories(self) -> Iterable[RoomCategory]:
        self._ensure_defaults()
        return self.room.room_categories.select_related("category").order_by("order_index", "id")

    def get_category_queryset(self):
        self._ensure_defaults()
        return Category.objects.filter(room_category_map__room=self.room).order_by(
            "room_category_map__order_index", "room_category_map__id"
        )

    def get_default_category(self):
        room_category = self._get_default_room_category()
        if room_category:
            return room_category.category
        return Category.get_default_category()

    def create_room_category(
        self,
        *,
        name: str,
        emoji: str,
        color: str | None = None,
        order_index: int | None = None,
        make_default: bool = False,
    ) -> RoomCategory:
        self._ensure_defaults()
        with transaction.atomic():
            desired_index = order_index if order_index is not None else self._next_order_index()
            if make_default:
                self._clear_default_marker()
            category = Category.objects.create(
                slug=self._build_unique_slug(name),
                name=name,
                emoji=emoji,
                color=color,
                order_index=desired_index,
            )
            room_category = RoomCategory.objects.create(
                room=self.room,
                category=category,
                order_index=desired_index,
                is_default=make_default,
            )
        return room_category

    def update_room_category(
        self, *, room_category_id: int, order_index: int, make_default: bool
    ) -> RoomCategory | None:
        self._ensure_defaults()
        room_category = self.room.room_categories.filter(id=room_category_id).first()
        if not room_category:
            return None
        room_category.order_index = order_index
        with transaction.atomic():
            if make_default:
                self._clear_default_marker()
            room_category.is_default = make_default
            room_category.save(update_fields=("order_index", "is_default"))
        return room_category

    def delete_room_category(self, room_category_id: int) -> None:
        self._ensure_defaults()
        with transaction.atomic():
            target = self.room.room_categories.select_for_update().filter(id=room_category_id).first()
            if not target:
                return
            was_default = target.is_default
            target.delete()
            if was_default:
                self._ensure_default_exists()

    def _ensure_defaults(self) -> None:
        if self.room.room_categories.exists():
            return
        with transaction.atomic():
            if self.room.room_categories.exists():
                return
            defaults = [
                RoomCategory(
                    room=self.room,
                    category=category,
                    order_index=index,
                    is_default=category.slug == DEFAULT_CATEGORY_SLUG,
                )
                for index, category in enumerate(Category.objects.order_by("order_index", "id"))
            ]
            if defaults:
                RoomCategory.objects.bulk_create(defaults, ignore_conflicts=True)
        self._ensure_default_exists()

    def _get_default_room_category(self) -> RoomCategory | None:
        return (
            self.room.room_categories.filter(is_default=True)
            .select_related("category")
            .order_by("order_index", "id")
            .first()
        )

    def _next_order_index(self) -> int:
        last = self.room.room_categories.order_by("-order_index", "-id").first()
        return (last.order_index + 1) if last else 0

    def get_next_order_index(self) -> int:
        self._ensure_defaults()
        return self._next_order_index()

    def _clear_default_marker(self) -> None:
        self.room.room_categories.filter(is_default=True).update(is_default=False)

    def _ensure_default_exists(self) -> None:
        if self.room.room_categories.filter(is_default=True).exists():
            return
        first = self.room.room_categories.order_by("order_index", "id").first()
        if first:
            first.is_default = True
            first.save(update_fields=("is_default",))

    def _build_unique_slug(self, name: str) -> str:
        base_slug = slugify(name) or "category"
        candidate = base_slug
        counter = 1
        while Category.objects.filter(slug=candidate).exists():
            candidate = f"{base_slug}-{counter}"
            counter += 1
        return candidate
