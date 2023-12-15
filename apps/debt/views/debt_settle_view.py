from django.utils import timezone
from django.views import generic
from django_context_decorator import context
from functools import cached_property

from apps.core import htmx
from apps.core.event_loop.runner import handle_message
from apps.debt.messages.events.debt_settled import DebtSettled
from apps.debt.models import Debt


class DebtSettleView(htmx.FormHtmxResponseMixin, generic.UpdateView):
    model = Debt
    fields = ("id", "settled", "settled_at")
    template_name = "debt/partials/_settle_debt_modal.html"

    hx_trigger = "loadDebtList"
    toast_success_message = "Debt successfully settled!"
    toast_error_message = "There was an error settling this debt"

    def form_valid(self, form):
        if self.object.settled:
            self.object.settled_at = timezone.now()

        handle_message(DebtSettled(context_data={"debt": self.object}))

        return super().form_valid(form)

    @context
    @cached_property
    def active_tab(self):
        return self.request.GET.get("active_tab", "debt")
