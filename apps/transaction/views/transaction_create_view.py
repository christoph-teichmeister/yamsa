import json

from django.http import HttpResponse
from django.views import generic

from apps.transaction.forms import TransactionCreateForm
from apps.transaction.models import ParentTransaction


class TransactionCreateView(generic.CreateView):
    model = ParentTransaction
    form_class = TransactionCreateForm
    template_name = "room/detail.html"

    def get_hx_trigger(self):
        return {
            "reloadTransactionList": True,
            "triggerToast": {"message": "Transaction created successfully", "type": "text-bg-success bg-gradient"},
        }

    def form_valid(self, form):
        self.object = form.save()

        response = HttpResponse(201)
        response["HX-Trigger"] = json.dumps(self.get_hx_trigger())
        return response
