from django.urls import reverse
from django.utils import timezone
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.debt.messages.events.debt_settled import DebtSettled
from apps.debt.models import Debt
from apps.debt.views.mixins.debt_base_context import DebtBaseContext


class DebtSettleView(DebtBaseContext, generic.UpdateView):
    model = Debt
    fields = ("id", "settled", "settled_at")
    template_name = "debt/settle.html"

    def form_valid(self, form):
        if self.object.settled:
            self.object.settled_at = timezone.now()

        handle_message(DebtSettled(context_data={"debt": self.object}))

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("debt-list", kwargs={"room_slug": self.request.room.slug})
