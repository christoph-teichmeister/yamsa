from django.db.models import F, Sum

from apps.account.models import User
from apps.currency.models import Currency
from apps.debt.dataclasses import SimpleDebtRow
from apps.transaction.models import ChildTransaction


class SimpleDebtService:
    """Who owes whom before optimisation: one row per debitor, creditor and currency.

    DebtOptimiseService nets these amounts across all room members, which is what makes its payment
    suggestions look unrelated to the expenses they came from. These rows are the unnetted
    counterpart, shown to explain that difference - they are gross amounts that ignore settlements
    and can never be paid off directly.
    """

    @staticmethod
    def get_rows(*, room_id, viewer_id) -> list[SimpleDebtRow]:
        # The explicit order_by() clears ChildTransaction's Meta ordering; an inherited ordering
        # field would otherwise join the GROUP BY and split the aggregate across extra rows.
        aggregates = list(
            ChildTransaction.objects.filter(parent_transaction__room_id=room_id)
            .exclude(paid_for_id=F("parent_transaction__paid_by_id"))
            .values("paid_for_id", "parent_transaction__paid_by_id", "parent_transaction__currency_id")
            .annotate(total_owed=Sum("value"))
            .filter(total_owed__gt=0)
            .order_by()
        )
        if not aggregates:
            return []

        user_ids = {row["paid_for_id"] for row in aggregates} | {
            row["parent_transaction__paid_by_id"] for row in aggregates
        }
        users = User.objects.in_bulk(user_ids)
        currencies = Currency.objects.in_bulk({row["parent_transaction__currency_id"] for row in aggregates})

        rows = [
            SimpleDebtRow(
                debitor=users[row["paid_for_id"]],
                creditor=users[row["parent_transaction__paid_by_id"]],
                value=row["total_owed"],
                currency=currencies[row["parent_transaction__currency_id"]],
                viewer_is_debitor=row["paid_for_id"] == viewer_id,
                viewer_is_creditor=row["parent_transaction__paid_by_id"] == viewer_id,
            )
            for row in aggregates
        ]
        # Same ordering as the optimised list, so switching modes does not reshuffle the page.
        rows.sort(key=lambda row: (row.currency.sign, row.debitor.name))
        return rows
