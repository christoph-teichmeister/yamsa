from django.forms import ModelForm

from apps.transaction.models import Transaction


class TransactionForm(ModelForm):
    class Meta:
        model = Transaction
        fields = (
            "description",
            "paid_by",
            "paid_for",
            "room",
            "value",
        )

    def clean(self):
        print("TransactionForm CLEAN")
        super().clean()
