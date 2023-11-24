from decimal import Decimal

from django import forms

from apps.account.models import User
from apps.core.event_loop.runner import handle_message
from apps.transaction.messages.events.transaction import ParentTransactionCreated
from apps.transaction.models import ParentTransaction, ChildTransaction


class TransactionCreateForm(forms.ModelForm):
    paid_for = forms.ModelMultipleChoiceField(queryset=User.objects.all())
    room_slug = forms.CharField()
    value = forms.DecimalField()

    class Meta:
        model = ParentTransaction
        fields = (
            "description",
            "currency",
            "paid_by",
            "room",
            "paid_for",
            "room_slug",
            "value",
        )

    def save(self, commit=True):
        instance: ParentTransaction = super().save(commit)

        value_per_debtor = round(
            Decimal(self.cleaned_data["value"] / self.cleaned_data["paid_for"].count()),
            2,
        )

        for debtor in self.cleaned_data["paid_for"]:
            ChildTransaction.objects.create(parent_transaction=instance, paid_for=debtor, value=value_per_debtor)

        handle_message(ParentTransactionCreated(context_data={"parent_transaction": instance, "room": instance.room}))

        return instance
