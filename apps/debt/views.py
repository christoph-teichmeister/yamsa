from django.urls import reverse
from django.views import generic

from apps.debt.forms import DebtSettleForm
from apps.debt.models import Debt


class DebtSettleView(generic.FormView):
    model = Debt
    form_class = DebtSettleForm
    template_name = "room/detail.html"

    def get_success_url(self):
        return reverse(
            viewname="room-detail", kwargs={"slug": self.request.POST.get("room_slug")}
        )

    def form_valid(self, form):
        form.mark_debt_as_settled()
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)
