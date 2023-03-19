from django.urls import reverse
from django.views import generic

from apps.moneyflow.models import MoneyFlow
from apps.transaction.forms import TransactionForm
from apps.transaction.models import Transaction


class TransactionCreateView(generic.CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "room/detail.html"

    def get_success_url(self):
        return reverse(viewname="room-detail", args=self.request.POST.get("room"))

    def post(self, request, *args, **kwargs):
        ret = super().post(request, *args, **kwargs)

        transaction: Transaction = self.object
        if transaction is not None:
            transaction.value = transaction.value / transaction.paid_for.count()
            transaction.save()

            # TODO CT: Maybe immediately optimise any existing flow upon transaction creation?
            existing_flows = MoneyFlow.objects.filter(user_id=transaction.paid_by)

        return ret
