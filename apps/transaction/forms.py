from _decimal import Decimal

from django import forms

from apps.core.event_loop.runner import handle_message
from apps.transaction.messages.events.transaction import TransactionCreated
from apps.transaction.models import Transaction


class TransactionCreateForm(forms.ModelForm):
    room_slug = forms.CharField()

    class Meta:
        model = Transaction
        fields = (
            "description",
            "currency",
            "paid_by",
            "paid_for",
            "room",
            "room_slug",
            "value",
        )

    def clean(self) -> dict:
        cleaned_data = super().clean()
        cleaned_data["value"] = round(
            Decimal(cleaned_data["value"] / cleaned_data["paid_for"].count()),
            2,
        )
        return cleaned_data

    def save(self, commit=True):
        instance: Transaction = super().save(commit)

        handle_message(TransactionCreated(context_data={"transaction": instance}))

        return instance
