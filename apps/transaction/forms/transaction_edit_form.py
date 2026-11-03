from decimal import Decimal

from ambient_toolbox.middleware.current_request import CurrentRequestMiddleware
from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.account.models import User
from apps.room.models import Room
from apps.transaction.forms.mixins.room_category_field import RoomCategoryFieldMixin
from apps.transaction.forms.mixins.split_shares import SplitSharesMixin
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.utils import split_total_across_paid_for


class TransactionEditForm(SplitSharesMixin, RoomCategoryFieldMixin, forms.ModelForm):
    total_value = forms.DecimalField(decimal_places=2, max_digits=10)

    category = RoomCategoryFieldMixin.build_category_field()

    # ChildTransaction fields
    paid_for = SimpleArrayField(forms.IntegerField())
    value = SimpleArrayField(forms.DecimalField(decimal_places=2, max_digits=10))
    child_transaction_id = SimpleArrayField(forms.IntegerField())

    class Meta:
        model = ParentTransaction
        fields = (
            # "total_value",
            "description",
            "further_notes",
            "paid_by",
            "paid_at",
            "currency",
            "category",
            # ChildTransaction fields
            "paid_for",
            "value",
            "child_transaction_id",
        )

    def __init__(self, *args: object, room: Room | None = None, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.narrow_category_field_to(room or getattr(self.instance, "room", None))
        self.fields["paid_by"].queryset = self._share_room_users()
        self._initial_total_value = self._current_total_value()
        self.fields["total_value"].initial = self._initial_total_value
        self.initial["total_value"] = self._initial_total_value

    def _share_room_users(self) -> QuerySet:
        return User.objects.filter(room=self.instance.room)

    def clean_child_transaction_id(self) -> list[int]:
        # 0 marks a new row; any other id is looked up on the instance when saving.
        submitted = set(self.cleaned_data["child_transaction_id"]) - {0}
        own = set(self.instance.child_transactions.filter(id__in=submitted).values_list("id", flat=True))
        if submitted != own:
            raise forms.ValidationError(_("Unknown share."), code="invalid_share")
        return self.cleaned_data["child_transaction_id"]

    def clean(self) -> dict:
        cleaned_data = super().clean()
        total_value = cleaned_data.get("total_value")
        paid_for = cleaned_data.get("paid_for")
        values = cleaned_data.get("value")
        share_ids = cleaned_data.get("child_transaction_id")

        # A missing key means its field already reported an error.
        if total_value is None or paid_for is None or values is None or share_ids is None:
            return cleaned_data
        if not self.shares_have_equal_length(share_ids, paid_for, values):
            return cleaned_data

        if total_value != self._initial_total_value:
            if not paid_for:
                self.add_error("paid_for", _("Select at least one debtor."))
                return cleaned_data
            values = split_total_across_paid_for(total_value, paid_for)

        if not self.share_amounts_are_valid(values):
            return cleaned_data

        share_ids, paid_for, values = self._merge_new_rows_into_debtor_rows(share_ids, paid_for, values)
        cleaned_data.update(
            child_transaction_id=share_ids, paid_for=paid_for, value=values, total_value=sum(values, Decimal("0.00"))
        )
        return cleaned_data

    @staticmethod
    def _merge_new_rows_into_debtor_rows(
        share_ids: list[int], paid_for: list[int], values: list[Decimal]
    ) -> tuple[list[int], list[int], list[Decimal]]:
        """Fold rows without an id into the debtor's other row, so each debtor is saved once.

        A debtor's anchor is their first row that already has an id, else their first new row.
        """
        rows = [[share_id, debtor, value] for share_id, debtor, value in zip(share_ids, paid_for, values, strict=True)]
        anchors: dict[int, list] = {}
        for row in rows:
            anchor = anchors.get(row[1])
            if anchor is None or (anchor[0] == 0 and row[0] != 0):
                anchors[row[1]] = row

        kept = []
        for row in rows:
            anchor = anchors[row[1]]
            if row[0] == 0 and anchor is not row:
                anchor[2] += row[2]
            else:
                kept.append(row)
        return [r[0] for r in kept], [r[1] for r in kept], [r[2] for r in kept]

    def save(self, commit: bool = True) -> ParentTransaction:
        # Only persists: the transaction boundary and the ParentTransactionUpdated event belong to
        # the view, after the rows are written (see AGENTS.md, #333).
        instance: ParentTransaction = super().save(commit)
        self._save_child_transactions(instance)
        return instance

    def _save_child_transactions(self, instance: ParentTransaction) -> None:
        request_user = CurrentRequestMiddleware.get_current_user()
        now = timezone.now()
        existing = {child.id: child for child in instance.child_transactions.all()}

        updated_child_transactions = []
        for child_transaction_id, debtor, value in self._shares_to_save(instance):
            if child_transaction_id == 0:
                ChildTransaction.objects.create(
                    parent_transaction=instance,
                    paid_for_id=debtor,
                    value=value,
                    created_by=request_user,
                    created_at=now,
                )
                continue

            child_transaction = existing[child_transaction_id]
            child_transaction.paid_for_id = debtor
            child_transaction.value = value
            child_transaction.lastmodified_by = request_user
            child_transaction.lastmodified_at = now
            updated_child_transactions.append(child_transaction)

        ChildTransaction.objects.bulk_update(
            objs=updated_child_transactions, fields=("paid_for", "value", "lastmodified_by", "lastmodified_at")
        )

    def _shares_to_save(self, instance: ParentTransaction) -> list[tuple[int, int, Decimal]]:
        # A share set to zero is how a debtor is taken out of the transaction: it is deleted here and
        # never reaches the create/update path.
        shares = []
        for child_transaction_id, debtor, value in zip(
            self.cleaned_data["child_transaction_id"],
            self.cleaned_data["paid_for"],
            self.cleaned_data["value"],
            strict=True,
        ):
            if value != 0:
                shares.append((child_transaction_id, debtor, value))
            elif child_transaction_id != 0:
                instance.child_transactions.filter(id=child_transaction_id).delete()
        return shares

    def _current_total_value(self) -> Decimal:
        raw_value = getattr(self.instance, "value", None)
        if raw_value is None:
            return Decimal("0.00")
        return Decimal(raw_value)
