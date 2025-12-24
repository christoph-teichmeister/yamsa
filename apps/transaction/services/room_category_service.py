from collections.abc import Iterable

from django.db import transaction
from django.db.models import F
from django.utils.text import slugify

from apps.room.models import Room
from apps.transaction.models import (
    BASE_CATEGORY_SLUGS,
    DEFAULT_CATEGORY_SLUG,
    Category,
    ParentTransaction,
    RoomCategory,
)


class RoomCategoryService:
    """
    Encapsulates the business logic for managing the categories configured on a Room.

    It ensures that every room starts with a canonical set of categories, keeps the order
    consistent, and enforces that one category is always marked as default. This service
    handles CRUD operations on the RoomCategory join model while maintaining related
    Category records (slug uniqueness, order, defaults).
    """

    room: Room

    def __init__(self, room: Room):
        """
        Initialize the service with the room whose categories we are managing.
        """
        self.room = room

    def get_categories(self) -> Iterable[RoomCategory]:
        """
        Return the room-specific categories with their related Category metadata,
        guaranteeing defaults exist before the query.
        """
        self._ensure_defaults()
        return self.room.room_categories.select_related("category").order_by("order_index", "id")

    def get_category_queryset(self):
        """
        Produce a queryset of Category objects associated with this room.
        The ordering mirrors the room-specific ordering for RoomCategory.
        """
        self._ensure_defaults()
        return Category.objects.filter(room_category_map__room=self.room).order_by(
            "room_category_map__order_index", "room_category_map__id"
        )

    def get_default_category(self):
        """
        Fetch the currently flagged default category for this room.
        Falls back to the global default if the room has no category marked.
        """
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
        """
        Create a new Category (with unique slug) and link it to the room via RoomCategory.

        Args:
            name: Label shown to users.
            emoji: Emoji used for visual identification.
            color: Optional color string for styling.
            order_index: Explicit order position; if omitted, append to the end.
            make_default: Whether to mark the new category as the room's default.
        """
        self._ensure_defaults()
        desired_index = order_index if order_index is not None else self._next_order_index()
        desired_index = self._clamp_create_index(desired_index)
        with transaction.atomic():
            if make_default:
                self._clear_default_marker()
            RoomCategory.objects.filter(room=self.room, order_index__gte=desired_index).update(
                order_index=F("order_index") + 1
            )
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
        """
        Update the RoomCategory metadata such as ordering/default flag.

        The method keeps the default constraint by clearing the previous default if
        this category is being promoted.
        """
        self._ensure_defaults()
        with transaction.atomic():
            room_category = self.room.room_categories.select_for_update().filter(id=room_category_id).first()
            if not room_category:
                return None
            total_categories = self.room.room_categories.count()
            max_index = max(total_categories - 1, 0)
            desired_index = max(0, min(order_index, max_index))
            current_index = room_category.order_index
            if desired_index < current_index:
                (
                    self.room.room_categories.filter(order_index__gte=desired_index, order_index__lt=current_index)
                    .exclude(id=room_category.id)
                    .update(order_index=F("order_index") + 1)
                )
            elif desired_index > current_index:
                (
                    self.room.room_categories.filter(order_index__gt=current_index, order_index__lte=desired_index)
                    .exclude(id=room_category.id)
                    .update(order_index=F("order_index") - 1)
                )
            if make_default:
                self._clear_default_marker()
            room_category.order_index = desired_index
            room_category.is_default = make_default
            room_category.save(update_fields=("order_index", "is_default"))
        return room_category

    def delete_room_category(self, room_category_id: int) -> Category | None:
        """
        Remove a RoomCategory and, if it was the default, promote another category.
        """
        self._ensure_defaults()
        with transaction.atomic():
            # Lock the row before deleting so we can safely check if it was the default.
            target = self.room.room_categories.select_for_update().filter(id=room_category_id).first()
            if not target:
                return None
            was_default = target.is_default
            shift_index = target.order_index
            deleted_category = target.category
            target.delete()
            self.room.room_categories.filter(order_index__gt=shift_index).update(order_index=F("order_index") - 1)
            if was_default:
                replacement = self._ensure_default_exists()
                replacement_category = replacement.category if replacement else Category.get_default_category()
                ParentTransaction.objects.filter(room=self.room, category=deleted_category).update(
                    category=replacement_category
                )
            return deleted_category

    def _ensure_defaults(self) -> None:
        """
        Populate the room with the base categories when none exist yet.

        Uses bulk creation to avoid repeated queries, and the method is safe to call
        from multiple locations because it re-checks after acquiring the transaction lock.
        """
        if self.room.room_categories.exists():
            return
        with transaction.atomic():
            if self.room.room_categories.exists():
                return
            base_categories = Category.objects.filter(slug__in=BASE_CATEGORY_SLUGS).order_by("order_index", "id")
            defaults = [
                RoomCategory(
                    room=self.room,
                    category=category,
                    order_index=index,
                    is_default=category.slug == DEFAULT_CATEGORY_SLUG,
                )
                for index, category in enumerate(base_categories)
            ]
            if defaults:
                # Bulk create avoids issuing a separate insert for each base category.
                RoomCategory.objects.bulk_create(defaults, ignore_conflicts=True)
        # Ensure there is always a default category because the room relies on it.
        self._ensure_default_exists()

    def _get_default_room_category(self) -> RoomCategory | None:
        """
        Helper that returns the RoomCategory marked as default (or None if missing).
        """
        return (
            self.room.room_categories.filter(is_default=True)
            .select_related("category")
            .order_by("order_index", "id")
            .first()
        )

    def _next_order_index(self) -> int:
        """
        Determine the next order index by looking up the highest current index.
        """
        last = self.room.room_categories.order_by("-order_index", "-id").first()
        # Start at zero if the room has no categories yet.
        return (last.order_index + 1) if last else 0

    def get_next_order_index(self) -> int:
        """
        Public-facing helper that ensures defaults exist before returning the next slot.
        """
        self._ensure_defaults()
        return self._next_order_index()

    def _clamp_create_index(self, desired_index: int) -> int:
        total = self.room.room_categories.count()
        return max(0, min(desired_index, total))

    def _clear_default_marker(self) -> None:
        """
        Clear the default flag from whichever category currently holds it.
        """
        self.room.room_categories.filter(is_default=True).update(is_default=False)

    def _ensure_default_exists(self) -> RoomCategory | None:
        """
        Guarantee there is always a default RoomCategory by promoting the first item if needed.
        """
        # Short-circuit if someone else already marked a default (common after create/update).
        if self.room.room_categories.filter(is_default=True).exists():
            return
        first = self.room.room_categories.order_by("order_index", "id").first()
        if first:
            first.is_default = True
            first.save(update_fields=("is_default",))
            return first
        return None

    def _build_unique_slug(self, name: str) -> str:
        """
        Generate a slugified identifier for a new Category, avoiding collisions.
        """
        base_slug = slugify(name) or "category"
        candidate = base_slug
        counter = 1
        # Keep appending incremental counters until we find one that does not clash.
        while Category.objects.filter(slug=candidate).exists():
            candidate = f"{base_slug}-{counter}"
            counter += 1
        return candidate
