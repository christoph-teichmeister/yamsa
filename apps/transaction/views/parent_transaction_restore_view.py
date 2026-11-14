from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import View

from apps.room.views.mixins import RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin
from apps.transaction.services.transaction_deletion_service import TransactionDeletionService


class ParentTransactionRestoreView(RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin, View):
    """The undo of a delete: POST-only, since it changes the room's debts."""

    http_method_names = ("post",)

    def post(self, request: HttpRequest, room_slug: str, pk: int) -> HttpResponse:
        restored = TransactionDeletionService.restore(pk=pk, room=request.room)
        if restored is None:
            request.toast_queue.error(_("Too late: the transaction is deleted for good."))
            return HttpResponseRedirect(reverse("transaction:list", kwargs={"room_slug": room_slug}))

        request.toast_queue.success(_('Restored "{description}".').format(description=restored.description))
        return HttpResponseRedirect(reverse("transaction:detail", kwargs={"room_slug": room_slug, "pk": restored.pk}))
