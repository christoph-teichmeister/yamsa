from django.http import StreamingHttpResponse
from django.utils import timezone
from django.views import View

from apps.core.views.mixins import CsvExportMixin
from apps.debt.models import Debt
from apps.debt.views.mixins.debt_base_context import DebtBaseContext
from apps.room.views.mixins import RoomMembershipRequiredMixin


class DebtExportView(RoomMembershipRequiredMixin, DebtBaseContext, CsvExportMixin, View):
    """Return CSV exports of unsettled debts for the user's room."""

    HEADER = ["debitor", "creditor", "amount", "currency"]

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

    def _write_rows(self, writer, buffer, debts, timestamp):
        for debt in debts:
            row = [
                self._safe(debt.debitor.name),
                self._safe(debt.creditor.name),
                f"{debt.value:.2f}",
                debt.currency.sign or debt.currency.code or "",
            ]
            writer.writerow(row)
            yield self._pop_buffer(buffer)
