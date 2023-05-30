from django.db.models import F
from django.urls import reverse
from django.views import generic

from apps.transaction.forms import TransactionCreateForm
from apps.transaction.models import Transaction


class TransactionCreateView(generic.CreateView):
    model = Transaction
    form_class = TransactionCreateForm
    template_name = "room/detail.html"

    def get_success_url(self):
        return reverse(
            viewname="room-detail", kwargs={"slug": self.request.POST.get("room_slug")}
        )


class TransactionListHTMXView(generic.ListView):
    model = Transaction
    context_object_name = "room_transactions"
    template_name = "transaction/_list.html"

    def get_queryset(self):
        room_slug = self.kwargs.get("slug")
        return (
            self.model.objects.filter(room__slug=room_slug)
            .select_related("paid_by", "room")
            .prefetch_related("paid_for")
            .annotate(
                paid_by_name=F("paid_by__name"),
                paid_for_name=F("paid_for__name"),
                currency_sign=F("currency__sign"),
            )
            .values(
                "id",
                "description",
                "value",
                "currency_sign",
                "paid_by_name",
                "paid_for_name",
                "created_at",
            )
        )
