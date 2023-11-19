from django import forms
from django.contrib.postgres.forms import SimpleArrayField
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
        instance: ParentTransaction = super().save(commit)
        request_user = self.data.get("request_user")

        updated_child_transactions = ()
        for index, child_transaction_id in enumerate(self.cleaned_data["child_transaction_id"]):
            debtor = self.cleaned_data["paid_for"][index]
            value = self.cleaned_data["value"][index]

            update_value_of_child_transaction = (
                len(list(filter(lambda debtor_id: debtor_id == debtor, self.cleaned_data["paid_for"]))) > 1
            ) and child_transaction_id == 0
            # We send id=0 with every child_transaction which is to be created
            add_child_transaction = child_transaction_id == 0 and not update_value_of_child_transaction
            edit_child_transaction = not add_child_transaction

            if edit_child_transaction or update_value_of_child_transaction:
                child_transaction = (
                    instance.child_transactions.get(id=child_transaction_id)
                    if not update_value_of_child_transaction
                    else instance.child_transactions.get(paid_for=debtor)
                )
                child_transaction.paid_for_id = debtor
                child_transaction.value = (
                    value if not update_value_of_child_transaction else (child_transaction.value + value)
                )

                child_transaction.lastmodified_by = request_user
                child_transaction.lastmodified_at = timezone.now()

                updated_child_transactions = (
                    *tuple(filter(lambda ct: ct.id != child_transaction.id, updated_child_transactions)),
                    child_transaction,
                )

            if add_child_transaction:
                ChildTransaction.objects.create(
                    parent_transaction=instance,
                    paid_for_id=debtor,
                    value=value,
                    created_by=request_user,
                    created_at=timezone.now(),
                )

        ChildTransaction.objects.bulk_update(
            objs=updated_child_transactions, fields=("paid_for", "value", "lastmodified_by", "lastmodified_at")
        )

        handle_message(ParentTransactionUpdated(context_data={"parent_transaction": instance}))

        return instance
