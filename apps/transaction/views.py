from django.urls import reverse
from django.views import generic

from apps.transaction.forms import TransactionForm
from apps.transaction.models import Transaction


class TransactionCreateView(generic.CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "room/detail.html"

    def get_success_url(self):
        return reverse(viewname="room-detail", kwargs={"slug": self.request.POST.get("room_slug")})

    def form_invalid(self, form):
        ret = super().form_invalid(form)
        return ret
