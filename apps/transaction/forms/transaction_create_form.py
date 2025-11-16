from decimal import Decimal

from django import forms
from django.db import transaction

from apps.account.models import User
from apps.core.event_loop.runner import handle_message
from apps.transaction.messages.events.transaction import ParentTransactionCreated
from apps.transaction.models import Category, ChildTransaction, ParentTransaction
from apps.transaction.utils import split_total_across_paid_for


class TransactionCreateForm(forms.ModelForm):
    paid_for = forms.ModelMultipleChoiceField(queryset=User.objects.all())
    room_slug = forms.CharField()
    value = forms.DecimalField()
    category = forms.ModelChoiceField(
        queryset=Category.objects.order_by("order_index", "id"),
        empty_label=None,
        required=False,
    )

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
            "category",
        )

    @transaction.atomic
    def save(self, commit=True):
        instance: ParentTransaction = super().save(commit)

        total_value = Decimal(self.cleaned_data["value"])
        paid_for_entries = list(self.cleaned_data["paid_for"])
        shares = split_total_across_paid_for(total_value, paid_for_entries)
        for debtor, share in zip(paid_for_entries, shares, strict=False):
            ChildTransaction.objects.create(parent_transaction=instance, paid_for=debtor, value=share)

        handle_message(ParentTransactionCreated(context_data={"parent_transaction": instance, "room": instance.room}))

        return instance
