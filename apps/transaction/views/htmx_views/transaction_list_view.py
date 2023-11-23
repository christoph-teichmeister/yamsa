from django.views import generic

from apps.room.views.mixins.room_specific_mixin import RoomSpecificMixin
from apps.transaction.models import ParentTransaction


class TransactionListHTMXView(RoomSpecificMixin, generic.ListView):
    model = ParentTransaction
    context_object_name = "parent_transactions"
    template_name = "transaction/_list.html"

    def get_queryset(self):
        return self.model.objects.filter(room=self._room)
