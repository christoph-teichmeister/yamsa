from django.urls import reverse
from django.views import generic

from apps.transaction.forms import TransactionCreateForm
from apps.transaction.models import ParentTransaction


class TransactionCreateView(generic.CreateView):
    model = ParentTransaction
    form_class = TransactionCreateForm
    template_name = "room/detail.html"

    def get_success_url(self):
        return reverse(viewname="room-detail", kwargs={"slug": self.request.POST.get("room_slug")})
