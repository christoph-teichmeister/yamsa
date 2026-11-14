from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.debt.messages.events.debt_payment_rejected import DebtPaymentRejected
from apps.debt.models import Debt
from apps.room.views.mixins import RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin


class DebtReopenView(RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin, generic.View):
    """Send a debt awaiting confirmation back to open: the creditor rejects it, the debitor withdraws it."""

    http_method_names = ("post",)

    def post(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        debt = get_object_or_404(Debt, pk=kwargs["pk"], room=request.room)
        if request.user.pk not in {debt.debitor_id, debt.creditor_id}:
            raise PermissionDenied(_("Only the people this debt is between can change it."))

        with transaction.atomic():
            # Locked so a confirmation racing this request cannot be undone by it.
            debt = Debt.objects.select_for_update().get(pk=debt.pk)
            changed = debt.reopen()

        # A withdrawal tells nobody: the creditor was only asked to confirm, and the row simply reads open again.
        if changed and request.user.pk == debt.creditor_id:
            handle_message(DebtPaymentRejected(context_data={"debt": debt}))

        return HttpResponseRedirect(reverse("debt:list", kwargs={"room_slug": request.room.slug}))
