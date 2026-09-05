from decimal import Decimal

from django.db import models
from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce

# Matches Debt.value; without an explicit output_field Coalesce raises "Expression contains mixed types".
_ZERO_AMOUNT = Value(Decimal("0"), output_field=DecimalField(max_digits=10, decimal_places=2))


class DebtQuerySet(models.QuerySet):
    """Custom implementation of QuerySet"""

    def filter_open(self):
        return self.filter(settled=False)

    def filter_involving_user(self, *, user_id: int):
        return self.filter(Q(debitor_id=user_id) | Q(creditor_id=user_id))

    def aggregate_balance_per_room_and_currency(self, *, user_id: int):
        """Return one row per (room, currency) holding the user's gross debit and credit side.

        Grouping by currency is mandatory: the project has no exchange rates, so amounts of
        different currencies must never be added up.

        The explicit order_by() clears any inherited ordering - an annotated ordering field
        would otherwise join the GROUP BY and split the aggregate across extra rows.

        A debt naming the user as debitor or creditor always belongs to a room the user can
        see, so no additional room filter is needed.
        """
        return (
            self.values("room_id", "currency__sign")
            .annotate(
                currency_sign=F("currency__sign"),
                owed_by_user=Coalesce(Sum("value", filter=Q(debitor_id=user_id)), _ZERO_AMOUNT),
                owed_to_user=Coalesce(Sum("value", filter=Q(creditor_id=user_id)), _ZERO_AMOUNT),
            )
            .order_by("currency__sign")
        )
