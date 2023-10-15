from django.urls import reverse
from django.utils import timezone
from django.views import generic

from apps.debt.models import Debt


class DebtSettleView(generic.UpdateView):
    model = Debt
    fields = (
        "id",
        "settled",
        "settled_at",
    )
    template_name = "room/detail.html"

    def get_success_url(self):
        return reverse(viewname="room-detail", kwargs={"slug": self.request.POST.get("room_slug")})

    def form_valid(self, form):
        if self.object.settled:
            self.object.settled_at = timezone.now()
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)
