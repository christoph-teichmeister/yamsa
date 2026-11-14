from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import QuerySet
from django.forms import BaseModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import generic
from django_context_decorator import context

from apps.core.event_loop.runner import handle_message
from apps.debt.messages.events.debt_marked_paid import DebtMarkedPaid
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
            # Locked so two simultaneous posts cannot both see the old state and notify twice.
            debt = Debt.objects.select_for_update().get(pk=self.object.pk)
            # The creditor's word settles the debt; the debitor can only claim to have paid.
            by_creditor = self.request.user.pk == debt.creditor_id
            changed = debt.settle() if by_creditor else debt.mark_as_paid()
        self.object = debt

        # Only after the commit, and only for a real change: re-posting says nothing new.
        if changed:
            event = (
                DebtSettled(context_data={"debt": debt, "settled_by": self.request.user})
                if by_creditor
                else DebtMarkedPaid(context_data={"debt": debt})
            )
            handle_message(event)

        return HttpResponseRedirect(self.get_success_url())

    @context
    @property
    def viewer_is_creditor(self) -> bool:
        return self.request.user.pk == self.object.creditor_id

    def get_success_url(self) -> str:
        return reverse("debt:list", kwargs={"room_slug": self.request.room.slug})
