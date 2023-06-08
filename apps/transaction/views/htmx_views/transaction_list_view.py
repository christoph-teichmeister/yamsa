from ambient_toolbox.view_layer import htmx_mixins
from django.db.models import F
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.core.context_managers import measure_time_and_queries
from apps.room.models import Room
from apps.transaction.models import Transaction


class TransactionListHTMXView(htmx_mixins.HtmxResponseMixin, generic.ListView):
    model = Transaction
    context_object_name = "room_transactions"
    template_name = "transaction/_list.html"
    hx_trigger = {"reloadTransactionAddModal": True}

    @context
    @cached_property
    def room(self):
        return Room.objects.get(slug=self.kwargs.get("slug"))

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
