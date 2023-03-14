from django import forms

from apps.transaction.models import Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = (
            "description",
            "paid_by",
            "paid_for",
            "room",
            "value",
        )
