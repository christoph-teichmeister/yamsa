from collections.abc import Sequence
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _


class SplitSharesMixin:
    """Validation shared by the forms that submit a split as parallel `paid_for`/`value` arrays.

    The arrays are zipped by position, so a length mismatch would silently drop or misassign shares.
    """

    def _share_room_users(self) -> QuerySet:
        raise NotImplementedError

    def clean_paid_for(self) -> list[int]:
        # `paid_for` is a SimpleArrayField, so a `queryset` on it limits nothing: any id would pass.
        requested = self.cleaned_data["paid_for"]
        members = set(self._share_room_users().filter(id__in=requested).values_list("id", flat=True))
        if not set(requested) <= members:
            raise ValidationError(_("Every debtor must be a member of the room."), code="invalid_debtor")
        return requested

    def shares_have_equal_length(self, *columns: Sequence) -> bool:
        if len({len(column) for column in columns}) > 1:
            self.add_error("value", _("Every share needs a debtor and an amount."))
            return False
        return True

    def share_amounts_are_valid(self, values: Sequence[Decimal]) -> bool:
        if any(value < 0 for value in values):
            self.add_error("value", _("A share cannot be negative."))
            return False
        if values and not any(values):
            self.add_error("value", _("At least one share needs an amount above zero."))
            return False
        return True
