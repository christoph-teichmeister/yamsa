from django.urls import reverse
from django.views import generic

from apps.transaction.forms.transaction_create_form import TransactionCreateForm
from apps.transaction.models import ParentTransaction
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class TransactionCreateView(TransactionBaseContext, generic.CreateView):
    model = ParentTransaction
    form_class = TransactionCreateForm
    template_name = "transaction/create.html"

    _active_tab = "transaction"

    def get_success_url(self):
        return reverse("transaction-list", kwargs={"room_slug": self.request.room.slug})
