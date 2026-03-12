from django.db.models import Prefetch
from django.http import StreamingHttpResponse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.views import View

from apps.core.views.mixins import CsvExportMixin
from apps.room.views.mixins import RoomMembershipRequiredMixin
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class TransactionExportView(RoomMembershipRequiredMixin, TransactionBaseContext, CsvExportMixin, View):
    """Return CSV rows for each transaction paid inside the room."""

    HEADER = [_("Paid by"), _("Paid for"), _("Description"), _("Amount"), _("Currency"), _("Category"), _("Paid at")]

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
        filename = _("transactions") + f"-{slugify(room.name)}-{timestamp.strftime('%Y-%m-%d-%H-%M-%S')}.csv"

        response = StreamingHttpResponse(self._iter_rows(room, parents, timestamp), content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response

    def _write_rows(self, writer, buffer, parents, timestamp):
        for parent in parents:
            currency_value = parent.currency.sign or parent.currency.code or ""
            category_name = self._safe(parent.category.name if parent.category else "")
            paid_by = self._safe(parent.paid_by.name)
            description = self._safe(parent.description)
            paid_at = parent.paid_at.isoformat()

            for child in parent.child_transactions.all():
                row = [
                    paid_by,
                    self._safe(child.paid_for.name),
                    description,
                    f"{child.value:.2f}",
                    currency_value,
                    category_name,
                    paid_at,
                ]
                writer.writerow(row)
                yield self._pop_buffer(buffer)
