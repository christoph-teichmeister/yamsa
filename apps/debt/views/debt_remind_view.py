from datetime import datetime

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import date
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View

from apps.core.event_loop.runner import handle_message
from apps.debt.messages.events.debt_reminder_requested import DebtReminderRequested
from apps.debt.models import Debt
from apps.debt.services.manual_payment_reminder_service import ManualPaymentReminderService
from apps.debt.services.manual_reminder_too_soon_error import ManualReminderTooSoonError
from apps.room.views.mixins import RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin


class DebtRemindView(RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin, View):
    http_method_names = ("post",)

    def post(self, request: HttpRequest, pk: int, **kwargs: object) -> HttpResponse:
        debt = get_object_or_404(
            Debt.objects.select_related("debitor", "creditor", "currency", "room"), pk=pk, room=request.room
        )

        try:
            ManualPaymentReminderService.record(debt, request.user)
        except ManualReminderTooSoonError as error:
            request.toast_queue.warning(
                _("%(name)s was reminded recently. The next reminder is possible at %(time)s.")
                % {"name": debt.debitor.name, "time": self._format_time(error.next_available_at)}
            )
        else:
            # After the commit: push and mail are slow I/O that must not hold a DB connection open.
            handle_message(DebtReminderRequested(context_data={"debt": debt}))
            request.toast_queue.success(_("%(name)s has been reminded.") % {"name": debt.debitor.name})

        return HttpResponseRedirect(reverse("debt:list", kwargs={"room_slug": request.room.slug}))

    @staticmethod
    def _format_time(value: datetime) -> str:
        return date(timezone.localtime(value), "SHORT_DATETIME_FORMAT")
