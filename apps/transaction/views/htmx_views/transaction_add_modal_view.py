from django.db.models import F
from django.views import generic

from apps.core.context_managers import measure_time_and_queries
from apps.currency.models import Currency
from apps.room.models import UserConnectionToRoom, Room


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
