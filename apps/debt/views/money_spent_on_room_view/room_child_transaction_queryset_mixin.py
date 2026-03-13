from apps.transaction.models import ChildTransaction


class RoomChildTransactionQuerysetMixin:
    def get_base_queryset(self):
        return ChildTransaction.objects.filter(parent_transaction__room=self.request.room)
