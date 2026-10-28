from django.db import transaction
from django.db.models import QuerySet
from django.forms import BaseModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.debt.messages.events.debt_settled import DebtSettled
from apps.debt.models import Debt
from apps.debt.views.mixins.debt_base_context import DebtBaseContext
from apps.room.views.mixins import RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin


class DebtSettleView(RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin, DebtBaseContext, generic.UpdateView):
    model = Debt
    # `settled_at` is derived from `settled`, never taken from the request.
    fields = ("settled",)
    template_name = "debt/settle.html"

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(room=self.request.room)

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        became_settled = form.cleaned_data["settled"] and "settled" in form.changed_data

        with transaction.atomic():
            debt = form.save(commit=False)
            if became_settled:
                debt.settled_at = timezone.localdate()
            elif not debt.settled:
                debt.settled_at = None
            debt.save()
        self.object = debt

        # Only after the commit, and only for a newly settled debt: marking it unsettled or
        # re-posting an already settled one tells nobody anything.
        if became_settled:
            handle_message(DebtSettled(context_data={"debt": debt}))

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse("debt:list", kwargs={"room_slug": self.request.room.slug})
