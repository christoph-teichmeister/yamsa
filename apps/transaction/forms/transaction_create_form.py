from decimal import Decimal

from django import forms
from django.db import transaction

from apps.account.models import User
from apps.core.event_loop.runner import handle_message
from apps.transaction.messages.events.transaction import ParentTransactionCreated
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.utils import split_amount_exact


class TransactionCreateForm(forms.ModelForm):
    paid_for = forms.ModelMultipleChoiceField(queryset=User.objects.all())
    room_slug = forms.CharField()
    value = forms.DecimalField()

    class Meta:
        model = ParentTransaction
        fields = (
            "description",
            "further_notes",
            "currency",
            "paid_by",
            "paid_at",
            "room",
            "paid_for",
            "room_slug",
            "value",
        )

    @transaction.atomic
    def save(self, commit=True):
        instance: ParentTransaction = super().save(commit)

        total_value = Decimal(self.cleaned_data["value"])
        shares = split_amount_exact(total=total_value, shares=self.cleaned_data["paid_for"].count())
        for debtor, share in zip(self.cleaned_data["paid_for"], shares, strict=False):
            ChildTransaction.objects.create(parent_transaction=instance, paid_for=debtor, value=share)

        handle_message(ParentTransactionCreated(context_data={"parent_transaction": instance, "room": instance.room}))

        return instance
