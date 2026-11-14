from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.forms import BaseForm
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views import generic

from apps.room.views.mixins import RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin
from apps.transaction.constants import DELETE_UNDO_SECONDS
from apps.transaction.models import ParentTransaction
from apps.transaction.models.constants import FORMER_MEMBER_MESSAGE
from apps.transaction.services.transaction_deletion_service import TransactionDeletionService
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class ParentTransactionDeleteView(
    RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin, TransactionBaseContext, generic.DeleteView
):
    model = ParentTransaction
    template_name = "transaction/edit.html"

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(room=self.request.room)

    def get_object(self, queryset: QuerySet | None = None) -> ParentTransaction:
        # Deleting rebuilds the room's debts just like an edit, so it is closed for the same reason.
        parent_transaction = super().get_object(queryset)
        if parent_transaction.involves_former_member:
            raise PermissionDenied(FORMER_MEMBER_MESSAGE)
        return parent_transaction

    def get_success_url(self) -> str:
        return reverse(
            viewname="transaction:list",
            kwargs={"room_slug": self.request.room.slug},
        )

    def form_valid(self, form: BaseForm) -> HttpResponse:
        # Any earlier delete whose undo window has passed is made final here, which notifies the room.
        TransactionDeletionService.finalise_expired(self.request.room)
        TransactionDeletionService.trash(self.object, user=self.request.user)
        self.request.toast_queue.add_with_action(
            _('Deleted "{description}".').format(description=self.object.description),
            action_label=_("Undo"),
            action_url=reverse(
                "transaction:parent-transaction-restore",
                kwargs={"room_slug": self.request.room.slug, "pk": self.object.pk},
            ),
            duration_ms=DELETE_UNDO_SECONDS * 1000,
        )
        return HttpResponseRedirect(self.get_success_url())
