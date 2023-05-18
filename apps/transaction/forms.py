from django import forms

from apps.transaction.models import Transaction


class TransactionForm(forms.ModelForm):
    room_slug = forms.CharField()

    class Meta:
        model = Transaction
        fields = (
            "description",
            "paid_by",
            "paid_for",
            "room",
            "room_slug",
            "value",
        )
