from django.utils import timezone
from django.views import generic

from apps.core import htmx
from apps.debt.models import Debt


class DebtSettleView(htmx.FormHtmxResponseMixin, generic.UpdateView):
    model = Debt
    fields = ("id", "settled", "settled_at")
    template_name = "debt/partials/_settle_debt_modal.html"

    hx_trigger = "reloadDebtList"
    toast_success_message = "Debt successfully settled!"
    toast_error_message = "There was an error settling this debt"

    def form_valid(self, form):
        if self.object.settled:
            self.object.settled_at = timezone.now()
        return super().form_valid(form)
