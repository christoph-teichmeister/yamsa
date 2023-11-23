from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.room.views.mixins.room_specific_mixin import RoomSpecificMixin
from apps.transaction.models import ParentTransaction


class TransactionDetailHTMXView(RoomSpecificMixin, generic.DetailView):
    model = ParentTransaction
    context_object_name = "parent_transaction"
    template_name = "transaction/_detail.html"

    @context
    @cached_property
    def child_transactions(self):
        return self.object.child_transactions.all()

    @context
    @cached_property
    def active_tab(self):
        return "transaction"
