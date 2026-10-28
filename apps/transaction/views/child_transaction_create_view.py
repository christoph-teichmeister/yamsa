from django.db.models import QuerySet
from django.forms import BaseModelForm
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.account.models import User
from apps.room.views.mixins import RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class ChildTransactionCreateView(
    RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin, TransactionBaseContext, generic.CreateView
):
    template_name = "transaction/child_transaction_create.html"

    model = ChildTransaction
    fields = ("parent_transaction", "paid_for", "value")

    def get_form(self, form_class: type | None = None) -> BaseModelForm:
        form = super().get_form(form_class)
        form.fields["parent_transaction"].queryset = ParentTransaction.objects.filter(room=self.request.room)
        form.fields["paid_for"].queryset = User.objects.filter(room=self.request.room)
        return form

    @context
    @cached_property
    def room_users(self) -> QuerySet:
        return User.objects.filter(room=self.request.room)
