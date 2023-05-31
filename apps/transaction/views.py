from django.db.models import F
from django.urls import reverse
from django.views import generic

from apps.core.context_managers import measure_time_and_queries
from apps.currency.models import Currency
from apps.room.models import UserConnectionToRoom, Room
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

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["room"] = Room.objects.get(slug=self.kwargs.get("slug"))
        return context

    @measure_time_and_queries("TransactionListHTMXView.get_queryset()")
    def get_queryset(self):
        return (
            self.model.objects.filter(room__slug=self.kwargs.get("slug"))
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


class TransactionAddModalHTMXView(generic.TemplateView):
    template_name = "transaction/partials/transaction_add_modal.html"

    @measure_time_and_queries("TransactionAddModalHTMXView.get_context_data()")
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        room_slug = self.kwargs.get("slug")
        context["room_users"] = (
            UserConnectionToRoom.objects.filter(room__slug=room_slug)
            .select_related("user")
            .values("user_has_seen_this_room")
            .annotate(
                name=F("user__name"),
                id=F("user__id"),
                is_guest=F("user__is_guest"),
            )
            .order_by("user_has_seen_this_room", "name")
        )
        context["room"] = Room.objects.get(slug=room_slug)
        context["currency_signs"] = Currency.objects.all()

        return context
