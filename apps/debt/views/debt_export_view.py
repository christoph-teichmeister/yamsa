"""Streaming exports for room debts."""

import csv
import io

from django.http import StreamingHttpResponse
from django.utils import timezone
from django.views import View

from apps.debt.models import Debt
from apps.debt.views.mixins.debt_base_context import DebtBaseContext
from apps.room.views.mixins import RoomMembershipRequiredMixin


class DebtExportView(RoomMembershipRequiredMixin, DebtBaseContext, View):
    """Return CSV exports of unsettled debts for the user's room."""

    HEADER = ["debitor", "creditor", "amount", "currency", "settled", "settled_at"]

    def get(self, request, *args, **kwargs):
        """Build a streaming response containing metadata and unsettled debt rows."""
        room = request.room
        debts = (
            Debt.objects.filter(room=room, settled=False)
            .select_related("debitor", "creditor", "currency")
            .order_by("debitor__name", "creditor__name")
        )

        timestamp = timezone.now()
        filename = f"debts-{room.slug}-{timestamp.strftime('%Y%m%d%H%M%S')}.csv"
        response = StreamingHttpResponse(self._iter_rows(room, debts, timestamp), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    def _iter_rows(self, room, debts, timestamp):
        """Yield CSV chunks for the metadata, header, and debt rows."""
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

        for debt in debts:
            row = [
                debt.debitor.name,
                debt.creditor.name,
                f"{debt.value:.2f}",
                debt.currency.sign or debt.currency.code or "",
                str(debt.settled),
                debt.settled_at.isoformat() if debt.settled_at else "",
            ]
            writer.writerow(row)
            yield self._pop_buffer(buffer)

    def _pop_buffer(self, buffer):
        """Clear the writer buffer and return its contents."""
        value = buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        return value
