from django.db.models import Manager, Sum

from apps.debt.querysets import DebtQuerySet


class DebtManager(Manager.from_queryset(DebtQuerySet)):
    """Custom Implementation of Manager"""

    def get_total_money_of_currency_owed_to_others_for_a_room(self, *, debitor_id, currency_id, room_id):
        return self.filter(room_id=room_id, debitor_id=debitor_id, currency_id=currency_id).aggregate(
            total=Sum("value")
        )["total"]

    def get_total_money_of_currency_owed_by_others_for_a_room(self, *, creditor_id, room_id, currency_id):
        return self.filter(room_id=room_id, creditor_id=creditor_id, currency_id=currency_id).aggregate(
            total=Sum("value")
        )["total"]
