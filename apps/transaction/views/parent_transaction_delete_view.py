from django.db import transaction
from django.db.models import QuerySet
from django.forms import BaseForm
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.room.views.mixins import RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin
from apps.transaction.messages.events.transaction import ParentTransactionDeleted
from apps.transaction.models import ParentTransaction
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class ParentTransactionDeleteView(
    RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin, TransactionBaseContext, generic.DeleteView
):
    model = ParentTransaction
    template_name = "transaction/edit.html"

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(room=self.request.room)

    def get_success_url(self) -> str:
        return reverse(
            viewname="transaction:list",
            kwargs={"room_slug": self.request.room.slug},
        )

    def form_valid(self, form: BaseForm) -> HttpResponse:
        # The event follows the commit: its handlers recalculate debts from what is left (#333).
        with transaction.atomic():
            deleted = ParentTransactionDeleted.context_before_deletion(self.object, user_who_deleted=self.request.user)
            self.object.delete()

        handle_message(ParentTransactionDeleted(context_data=deleted))
        return HttpResponseRedirect(self.get_success_url())
