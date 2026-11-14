from django.db.models import DateTimeField, ExpressionWrapper, OuterRef, Q, QuerySet, Subquery
from django.utils import timezone
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.debt.dataclasses import SimpleDebtRow
from apps.debt.models import Debt, ReminderLog
from apps.debt.services.manual_payment_reminder_service import ManualPaymentReminderService
from apps.debt.services.simple_debt_service import SimpleDebtService
from apps.debt.views.mixins.debt_base_context import DebtBaseContext
from apps.room.views.mixins import RoomMembershipRequiredMixin
from apps.transaction.models import ParentTransaction


class DebtListView(RoomMembershipRequiredMixin, DebtBaseContext, generic.ListView):
    model = Debt
    context_object_name = "debts"
    template_name = "debt/list.html"

    MODE_OPTIMISED = "optimised"
    MODE_SIMPLE = "simple"
    MODES = (MODE_OPTIMISED, MODE_SIMPLE)
    DEFAULT_MODE = MODE_OPTIMISED

    @context
    @cached_property
    def debt_mode(self) -> str:
        mode = self.request.GET.get("mode", self.DEFAULT_MODE)
        # An unknown mode falls back rather than 404s: the value only picks a reading of the same
        # data, and a stale bookmark should still show the room's debts.
        return mode if mode in self.MODES else self.DEFAULT_MODE

    @context
    @property
    def showing_optimised_debts(self) -> bool:
        return self.debt_mode == self.MODE_OPTIMISED

    @context
    @property
    def has_transactions(self) -> bool:
        return ParentTransaction.objects.filter(room_id=self.request.room.id).exists()

    @context
    @property
    def active_debt_count(self) -> int:
        return self.model.objects.filter(room_id=self.request.room.id, settled=False).count()

    @context
    @property
    def payment_count_comparison(self) -> dict[str, int] | None:
        """How many payments the optimisation saves, or None when the number would mislead.

        Once a debt is settled the optimised list no longer covers the room's full history, while
        the unoptimised rows still do - comparing the two counts then overstates the saving, so the
        hint is dropped instead.
        """
        if self.model.objects.filter(room_id=self.request.room.id, settled=True).exists():
            return None

        optimised_count = self.active_debt_count
        simple_count = len(self._simple_debt_rows)
        if simple_count <= optimised_count:
            return None

        return {"optimised": optimised_count, "simple": simple_count}

    @cached_property
    def _simple_debt_rows(self) -> list[SimpleDebtRow]:
        return SimpleDebtService.get_rows(room_id=self.request.room.id, viewer_id=self.request.user.id)

    def get_queryset(self) -> list[SimpleDebtRow] | QuerySet:
        if not self.showing_optimised_debts:
            return self._simple_debt_rows

        # Each row phrases the debt from the viewer's side ("You owe X" / "X owes you"), so both
        # sides are resolved once in SQL rather than per row in the template.
        viewer_id = self.request.user.id
        # Non-null only while the viewer's cooldown for this debtor runs; the template shows when it ends.
        last_reminder = (
            ReminderLog.objects.filter(
                reminder_type=ReminderLog.ReminderType.MANUAL_DEBT,
                room_id=OuterRef("room_id"),
                debitor_id=OuterRef("debitor_id"),
                created_by_id=viewer_id,
                created_at__gt=timezone.now() - ManualPaymentReminderService.COOLDOWN,
            )
            .order_by("-created_at")
            .values("created_at")[:1]
        )
        return (
            self.model.objects.filter(room_id=self.request.room.id)
            .select_related("debitor", "creditor", "currency")
            .annotate(
                viewer_is_debitor=Q(debitor_id=viewer_id),
                viewer_is_creditor=Q(creditor_id=viewer_id),
                reminder_available_at=ExpressionWrapper(
                    Subquery(last_reminder) + ManualPaymentReminderService.COOLDOWN, output_field=DateTimeField()
                ),
            )
            .order_by("settled", "currency__sign", "debitor__name")
        )
