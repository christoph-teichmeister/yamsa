from django import forms

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
