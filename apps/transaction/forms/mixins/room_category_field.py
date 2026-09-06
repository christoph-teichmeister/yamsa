from django import forms
from django.db.models import QuerySet

from apps.room.models import Room
from apps.transaction.models import Category
from apps.transaction.services.room_category_service import RoomCategoryService


class RoomCategoryFieldMixin:
    """
    Shared ``category`` wiring for the transaction create and edit forms.

    Both offer the same choices over the same control, so which categories a room has and in
    what order lives here once instead of drifting apart in two form classes.
    """

    @staticmethod
    def build_category_field() -> forms.ModelChoiceField:
        """
        Produce the ``category`` field to declare in a form's own body.

        A field assigned on a plain mixin would be dropped: Django's form metaclass collects
        fields from the class body it processes and from bases that already carry
        ``declared_fields``, and a mixin is neither.
        """
        # The model field is NOT NULL and the chip picker renders the queryset directly, so a
        # blank choice could only ever be an option that fails validation.
        return forms.ModelChoiceField(
            queryset=Category.objects.order_by("order_index", "id"),
            empty_label=None,
        )

    def narrow_category_field_to(self, room: Room | None) -> None:
        """
        Restrict ``category`` to what ``room`` offers, in the order the room put them in.

        Called explicitly rather than from ``__init__`` because the two forms learn their room
        at different points: the create form from its caller before ``super().__init__()``, the
        edit form from ``self.instance`` only after it.
        """
        self.fields["category"].queryset = self._category_queryset(room)

    @staticmethod
    def _category_queryset(room: Room | None) -> QuerySet[Category]:
        if room:
            return RoomCategoryService(room=room).get_category_queryset()
        return Category.objects.order_by("order_index", "id")
