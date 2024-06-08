import copy
from decimal import Decimal

from django import forms

from apps.account.models import User
from apps.transaction.models import ChildTransaction, ParentTransaction


class TransactionCreateForm(forms.ModelForm):
    paid_for = forms.ModelMultipleChoiceField(queryset=User.objects.all())
    room_slug = forms.CharField()
    value = forms.DecimalField()

    _paid_for_everyone = False

    class Meta:
        model = ParentTransaction
        fields = (
            "description",
            "further_notes",
            "currency",
            "paid_by",
            "room",
            "paid_for",
            "room_slug",
            "value",
        )

    def __init__(self, *args, **kwargs):
        self._paid_for_everyone = kwargs.get("data", {"paid_for": None})["paid_for"] == "0"
        if not self._paid_for_everyone:
            super().__init__(*args, **kwargs)
        else:
            new_data = copy.deepcopy(kwargs.get("data"))
            kwargs.pop("data")
            new_data["paid_for"] = self.base_fields["paid_for"].choices.queryset.values_list("id", flat=True)[0]

            super().__init__(*args, **kwargs, data=new_data)

    def save(self, commit=True):
        instance: ParentTransaction = super().save(commit)

        if self._paid_for_everyone:
            self.cleaned_data["paid_for"] = instance.room.users.all()

        value_per_debtor = round(
            Decimal(self.cleaned_data["value"] / self.cleaned_data["paid_for"].count()),
            2,
        )

        for debtor in self.cleaned_data["paid_for"]:
            ChildTransaction.objects.create(parent_transaction=instance, paid_for=debtor, value=value_per_debtor)

        return instance
