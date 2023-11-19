from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.db import transaction
from django.utils import timezone

from apps.account.models import User
from apps.core.event_loop.runner import handle_message
from apps.transaction.messages.events.transaction import ParentTransactionUpdated
from apps.transaction.models import ParentTransaction, ChildTransaction


class TransactionEditForm(forms.ModelForm):
    # TODO CT: Uncomment if ever allowing to edit total_value of transaction
    # total_value = forms.DecimalField(decimal_places=2, max_digits=10)

    # ChildTransaction fields
    paid_for = SimpleArrayField(forms.IntegerField())
    value = SimpleArrayField(forms.DecimalField(decimal_places=2, max_digits=10))
    child_transaction_id = SimpleArrayField(forms.IntegerField())

    class Meta:
        model = ParentTransaction
        fields = (
            # "total_value",
            "description",
            "paid_by",
            "currency",
            # ChildTransaction fields
            "paid_for",
            "value",
            "child_transaction_id",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        room_users_qs = User.objects.filter(room=self.instance.room)

        self.fields["paid_by"].queryset = room_users_qs
        self.fields["paid_for"].queryset = room_users_qs

    def save(self, commit=True):
        # Call the super class's save method and get the ParentTransaction instance
        instance: ParentTransaction = super().save(commit)

        # Get the user making the request
        request_user = self.data.get("request_user")

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

        # Handle any necessary post-update actions
        handle_message(ParentTransactionUpdated(context_data={"parent_transaction": instance}))

        # Return the saved ParentTransaction instance
        return instance
