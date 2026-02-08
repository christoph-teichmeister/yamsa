"""Streaming exports for room transactions."""

import csv
import io

from django.db.models import Prefetch
from django.http import StreamingHttpResponse
from django.utils import timezone
from django.views import View

from apps.room.views.mixins import RoomMembershipRequiredMixin
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class TransactionExportView(RoomMembershipRequiredMixin, TransactionBaseContext, View):
    """Return CSV rows for each transaction paid inside the room."""

    HEADER = ["paid_by", "paid_for", "description", "amount", "currency", "category", "paid_at"]

    def get(self, request, *args, **kwargs):
        """Stream room transactions while respecting prefetching and metadata."""
        room = request.room
        parents = (
            ParentTransaction.objects.filter(room=room)
            .select_related("paid_by", "currency", "category")
            .prefetch_related(
                Prefetch(
                    "child_transactions",
                    queryset=ChildTransaction.objects.select_related("paid_for"),
                )
            )
            .order_by("-paid_at", "-id")
        )

        timestamp = timezone.now()
        filename = f"transactions-{room.slug}-{timestamp.strftime('%Y%m%d%H%M%S')}.csv"
        response = StreamingHttpResponse(self._iter_rows(room, parents, timestamp), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    def _iter_rows(self, room, parents, timestamp):
        """Yield CSV metadata, header, and transaction rows in streaming chunks."""
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        metadata = [
            ["Room Slug", room.slug],
            ["Room Name", room.name],
            ["Export Timestamp", timestamp.isoformat()],
        ]

        for row in metadata:
            writer.writerow(row)
            yield self._pop_buffer(buffer)

        writer.writerow([])
        yield self._pop_buffer(buffer)

        writer.writerow(self.HEADER)
        yield self._pop_buffer(buffer)

        for parent in parents:
            currency_value = parent.currency.sign or parent.currency.code or ""
            category_name = parent.category.name if parent.category else ""
            for child in parent.child_transactions.all():
                row = [
                    parent.paid_by.name,
                    child.paid_for.name,
                    parent.description,
                    f"{child.value:.2f}",
                    currency_value,
                    category_name,
                    parent.paid_at.isoformat(),
                ]
                writer.writerow(row)
                yield self._pop_buffer(buffer)

    def _pop_buffer(self, buffer):
        """Return and reset the accumulated CSV buffer."""
        value = buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        return value
