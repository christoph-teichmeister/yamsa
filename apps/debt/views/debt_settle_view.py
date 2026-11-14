from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet
from django.forms import BaseModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
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

    def get_object(self, queryset: QuerySet | None = None) -> Debt:
        debt = super().get_object(queryset)
        if self.request.user.pk not in {debt.debitor_id, debt.creditor_id}:
            raise PermissionDenied(_("Only the people this debt is between can settle it."))
        return debt

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        # Settling is one-way: debts are folded back into the optimisation as settled, so there is
        # no un-settle path that would keep the balances right.
        if not form.cleaned_data["settled"]:
            raise PermissionDenied(_("A settled debt cannot be reopened."))

        with transaction.atomic():
            # Locked so two simultaneous posts cannot both see "unsettled" and notify twice.
            debt = Debt.objects.select_for_update().get(pk=self.object.pk)
            became_settled = not debt.settled
            if became_settled:
                debt.settled = True
                # `settled_at` is derived, never taken from the request.
                debt.settled_at = timezone.localdate()
                debt.save()
        self.object = debt

        # Only after the commit, and only for a newly settled debt: re-posting an already settled
        # one tells nobody anything.
        if became_settled:
            handle_message(DebtSettled(context_data={"debt": debt, "settled_by": self.request.user}))

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse("debt:list", kwargs={"room_slug": self.request.room.slug})
