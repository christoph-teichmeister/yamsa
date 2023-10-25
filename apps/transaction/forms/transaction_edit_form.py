from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.utils import timezone

from apps.account.models import User
from apps.core.event_loop.runner import handle_message
from apps.transaction.messages.events.transaction import ParentTransactionUpdated
from apps.transaction.models import ParentTransaction, ChildTransaction


class TransactionEditForm(forms.ModelForm):
    # total_value = forms.DecimalField(decimal_places=2, max_digits=10)

    # ChildTransaction fields
    paid_for = forms.ModelMultipleChoiceField(queryset=User.objects.all())
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

        updated_child_transactions = ()
        for index, debtor in enumerate(self.cleaned_data["paid_for"]):
            edit_child_transaction = False
            add_child_transaction = False
            try:
                # Try to access the id at the current indexes place, if it exists, then we know that we _edited_ a
                # child transaction, if not, then we added a child_transaction
                _ = self.cleaned_data["child_transaction_id"][index]
                if _ == 0:
                    # We send id=0 with every child_transaction which is to be created
                    raise IndexError

                edit_child_transaction = True
            except IndexError:
                add_child_transaction = True

            value = self.cleaned_data["value"][index]
            request_user = self.data.get("request_user")

            if edit_child_transaction:
                child_transaction = ChildTransaction.objects.get(id=self.cleaned_data["child_transaction_id"][index])
                child_transaction.paid_for = debtor
                child_transaction.value = value

                child_transaction.lastmodified_by = request_user
                child_transaction.lastmodified_at = timezone.now()

                updated_child_transactions += (child_transaction,)

            if add_child_transaction:
                ChildTransaction.objects.create(
                    parent_transaction=instance,
                    paid_for=debtor,
                    value=value,
                    created_by=request_user,
                    created_at=timezone.now(),
                )

        ChildTransaction.objects.bulk_update(
            objs=updated_child_transactions, fields=("paid_for", "value", "lastmodified_by", "lastmodified_at")
        )

        handle_message(ParentTransactionUpdated(context_data={"parent_transaction": instance}))

        return instance
