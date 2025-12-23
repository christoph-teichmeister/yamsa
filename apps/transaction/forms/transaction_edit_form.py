from decimal import Decimal

from ambient_toolbox.middleware.current_request import CurrentRequestMiddleware
from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.db import transaction
from django.utils import timezone

from apps.account.models import User
from apps.core.event_loop.runner import handle_message
from apps.transaction.messages.events.transaction import ParentTransactionUpdated
from apps.transaction.models import Category, ChildTransaction, ParentTransaction
from apps.transaction.services.room_category_service import RoomCategoryService
from apps.transaction.utils import split_total_across_paid_for


class TransactionEditForm(forms.ModelForm):
    total_value = forms.DecimalField(decimal_places=2, max_digits=10)

    category = forms.ModelChoiceField(
        queryset=Category.objects.order_by("order_index", "id"),
        empty_label=None,
        required=False,
    )

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

    def __init__(self, *args, room=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._room = room or getattr(self.instance, "room", None)
        self.fields["category"].queryset = self._build_category_queryset()
        room_users_qs = User.objects.filter(room=self.instance.room)

        self.fields["paid_by"].queryset = room_users_qs
        self.fields["paid_for"].queryset = room_users_qs
        self._initial_total_value = self._current_total_value()
        self.fields["total_value"].initial = self._initial_total_value
        self.initial["total_value"] = self._initial_total_value

    def clean(self):
        cleaned_data = super().clean()
        total_value = cleaned_data.get("total_value")

        if total_value is None:
            return cleaned_data

        values = cleaned_data.get("value") or []
        paid_for_entries = cleaned_data.get("paid_for") or []
        sum_values = sum(values, Decimal("0.00"))
        total_changed = total_value != self._initial_total_value

        if total_changed and paid_for_entries:
            recalculated_values = split_total_across_paid_for(total_value, paid_for_entries)
            cleaned_data["value"] = recalculated_values
            cleaned_data["total_value"] = total_value
        elif sum_values != total_value:
            cleaned_data["total_value"] = sum_values

        return cleaned_data

    def save(self, commit=True):
        # Call the super class's .save() and get the ParentTransaction instance
        instance: ParentTransaction = super().save(commit)

        self._save_child_transactions(instance)

        # Handle any necessary post-update actions
        handle_message(ParentTransactionUpdated(context_data={"parent_transaction": instance, "room": instance.room}))

        # Return the saved ParentTransaction instance
        return instance

    def _save_child_transactions(self, instance: ParentTransaction):
        # Get the user making the request
        request_user = CurrentRequestMiddleware.get_current_user()

        # Initialize an empty list to keep track of updated ChildTransaction instances
        updated_child_transactions = []

        # Iterate over the submitted child transactions
        for index, child_transaction_id in enumerate(self.cleaned_data["child_transaction_id"]):
            debtor = self.cleaned_data["paid_for"][index]
            value = self.cleaned_data["value"][index]

            # Check if the child transaction is being updated or if its value is being modified
            update_value_of_child_transaction = (
                self.cleaned_data["paid_for"].count(debtor) > 1 and child_transaction_id == 0
            )

            # Check if a new child transaction is being added
            add_child_transaction = child_transaction_id == 0 and not update_value_of_child_transaction

            # Check if an existing child transaction is being edited
            edit_child_transaction = not add_child_transaction

            if edit_child_transaction or update_value_of_child_transaction:
                # Retrieve the child transaction to be updated
                child_transaction = (
                    instance.child_transactions.get(id=child_transaction_id)
                    if not update_value_of_child_transaction
                    else instance.child_transactions.get(paid_for=debtor)
                )

                # Update the child transaction fields
                child_transaction.paid_for_id = debtor
                child_transaction.value = (
                    child_transaction.value + value if update_value_of_child_transaction else value
                )
                child_transaction.lastmodified_by = request_user
                child_transaction.lastmodified_at = timezone.now()

                updated_child_transactions = (
                    *list(filter(lambda ct: ct.id != child_transaction.id, updated_child_transactions)),
                    child_transaction,
                )

            if add_child_transaction:
                # Create a new child transaction
                ChildTransaction.objects.create(
                    parent_transaction=instance,
                    paid_for_id=debtor,
                    value=value,
                    created_by=request_user,
                    created_at=timezone.now(),
                )

        # Use a bulk update to efficiently update multiple child transactions
        with transaction.atomic():
            ChildTransaction.objects.bulk_update(
                objs=updated_child_transactions, fields=("paid_for", "value", "lastmodified_by", "lastmodified_at")
            )

    def _current_total_value(self) -> Decimal:
        raw_value = getattr(self.instance, "value", None)
        if raw_value is None:
            return Decimal("0.00")
        return Decimal(raw_value)

    def _build_category_queryset(self):
        if self._room:
            return RoomCategoryService(room=self._room).get_category_queryset()
        return Category.objects.order_by("order_index", "id")
