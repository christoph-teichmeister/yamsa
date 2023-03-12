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
        print()
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        print("TransactionCreateView FORM_VALID")
        return super().form_valid(form)

    def form_invalid(self, form):
        print("TransactionCreateView FORM_INVALID")
        return super().form_invalid(form)
