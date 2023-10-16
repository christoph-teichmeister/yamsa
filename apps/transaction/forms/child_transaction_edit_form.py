from django import forms

from apps.account.models import User
from apps.transaction.models import ChildTransaction


class ChildTransactionEditForm(forms.ModelForm):
    # TODO CT: Delete
    class Meta:
        model = ChildTransaction
        fields = ("id", "paid_for", "value", "parent_transaction")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        initial = kwargs.get("initial")
        if initial is not None:
            self.fields["paid_for"].queryset = User.objects.filter(room=initial.get("room"))
