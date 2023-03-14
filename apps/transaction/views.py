from django.urls import reverse
from django.views import generic

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
        transaction.value = transaction.value / transaction.paid_for.count()
        transaction.save()

        return ret
