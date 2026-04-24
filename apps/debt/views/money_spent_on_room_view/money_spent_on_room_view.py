from django.db.models import F, Max, QuerySet, Sum
from django.views import generic
from django_context_decorator import context

from apps.debt.models import Debt
from apps.debt.views.mixins.debt_base_context import DebtBaseContext
from apps.debt.views.money_spent_on_room_view.room_child_transaction_queryset_mixin import (
    RoomChildTransactionQuerysetMixin,
)


class MoneySpentOnRoomView(RoomChildTransactionQuerysetMixin, DebtBaseContext, generic.TemplateView):
    template_name = "transaction/partials/_money_spent_on_room.html"

    @context
    @property
    def money_spent_per_person_qs(self) -> QuerySet[dict[str, object]]:
        return (
            self.get_base_queryset()
            .values("parent_transaction__paid_by__name", "parent_transaction__currency__sign")
            .annotate(
                paid_by_name=F("parent_transaction__paid_by__name"),
                currency_sign=F("parent_transaction__currency__sign"),
                total_spent_per_person=Sum("value"),
            )
            .order_by("parent_transaction__paid_by__name")
        )

    @context
    @property
    def total_money_spent(self) -> QuerySet[dict[str, object]]:
        return (
            self.get_base_queryset()
            .values("parent_transaction__currency__sign")
            .annotate(currency_sign=F("parent_transaction__currency__sign"), total_spent=Sum("value"))
        )

    @context
    @property
    def money_covered_for_person_qs(self) -> QuerySet[dict[str, object]]:
        """Gross amount paid by others for each person (excluding self-paid shares)."""
        return (
            self.get_base_queryset()
            .exclude(paid_for=F("parent_transaction__paid_by"))
            .values("paid_for__name", "parent_transaction__currency__sign")
            .annotate(
                currency_sign=F("parent_transaction__currency__sign"),
                total_covered_for_person=Sum("value"),
            )
            .order_by("paid_for__name")
        )

    @context
    @property
    def open_debts_per_person_qs(self) -> QuerySet[dict[str, object]]:
        """Actual outstanding debts after optimisation, grouped by debtor and currency."""
        return (
            Debt.objects.filter(room_id=self.request.room.id, settled=False)
            .values("debitor__name", "currency__sign")
            .annotate(
                debitor_name=F("debitor__name"),
                currency_sign=F("currency__sign"),
                total_open_debt=Sum("value"),
            )
            .order_by("debitor__name")
        )

    @context
    @property
    def max_open_debt_per_currency(self) -> dict[str, object]:
        """Max open debt value per currency – used for bar scaling in the template."""
        qs = (
            Debt.objects.filter(room_id=self.request.room.id, settled=False)
            .values("currency__sign")
            .annotate(currency_sign=F("currency__sign"), max_debt=Max("value"))
        )
        return {row["currency_sign"]: row["max_debt"] for row in qs}
