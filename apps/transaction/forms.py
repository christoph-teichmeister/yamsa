from _decimal import Decimal

from django import forms
from django.utils import timezone

from apps.core.event_loop.runner import handle_message
from apps.transaction.messages.commands.transaction import CreateTransaction
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

        # Mark any debts created because of this transaction, which belong to the debitor as settled, as a debitor
        # can not owe themself money
        instance.paid_by.owes_transactions.filter(user=instance.paid_by, transaction_id=instance.id).update(
            settled=True, settled_at=timezone.now()
        )

        from apps.moneyflow.models import MoneyFlow

        MoneyFlow.objects.create_or_update_flows_for_transaction(transaction=instance)

        handle_message(
            CreateTransaction(
                context_data={
                    "room": instance.room,
                    "value": instance.value,
                    "creditor": instance.paid_by,
                    "debitor": instance.paid_for,
                }
            )
        )

        return instance
