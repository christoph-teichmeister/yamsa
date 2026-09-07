from django.db.models import Q
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.debt.models import Debt
from apps.debt.services.simple_debt_service import SimpleDebtService
from apps.debt.views.mixins.debt_base_context import DebtBaseContext
from apps.transaction.models import ParentTransaction


class DebtListView(DebtBaseContext, generic.ListView):
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
    def has_transactions(self):
        return ParentTransaction.objects.filter(room_id=self.request.room.id).exists()

    @context
    @property
    def active_debt_count(self):
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
    def _simple_debt_rows(self):
        return SimpleDebtService.get_rows(room_id=self.request.room.id, viewer_id=self.request.user.id)

    def get_queryset(self):
        if not self.showing_optimised_debts:
            return self._simple_debt_rows

        # Each row phrases the debt from the viewer's side ("You owe X" / "X owes you"), so both
        # sides are resolved once in SQL rather than per row in the template.
        viewer_id = self.request.user.id
        return (
            self.model.objects.filter(room_id=self.request.room.id)
            .select_related("debitor", "creditor", "currency")
            .annotate(
                viewer_is_debitor=Q(debitor_id=viewer_id),
                viewer_is_creditor=Q(creditor_id=viewer_id),
            )
            .order_by("settled", "currency__sign", "debitor__name")
        )
