from decimal import Decimal

from django.db.models import Manager, Sum

from apps.debt.querysets import DebtQuerySet


class DebtManager(Manager.from_queryset(DebtQuerySet)):
    """Custom Implementation of Manager"""

    def get_total_money_of_currency_still_owed_to_others_for_a_room(self, *, debitor_id, currency_id, room_id):
        return self.filter(room_id=room_id, debitor_id=debitor_id, currency_id=currency_id, settled=False).aggregate(
            total=Sum("value")
        )["total"] or Decimal("0")

    def get_total_money_of_currency_still_owed_by_others_for_a_room(self, *, creditor_id, room_id, currency_id):
        return self.filter(room_id=room_id, creditor_id=creditor_id, currency_id=currency_id, settled=False).aggregate(
            total=Sum("value")
        )["total"] or Decimal("0")

    def get_total_money_of_currency_ever_owed_to_others_for_a_room(self, *, debitor_id, currency_id, room_id):
        return self.filter(room_id=room_id, debitor_id=debitor_id, currency_id=currency_id).aggregate(
            total=Sum("value")
        )["total"]

    def get_total_money_of_currency_ever_owed_by_others_for_a_room(self, *, creditor_id, room_id, currency_id):
        return self.filter(room_id=room_id, creditor_id=creditor_id, currency_id=currency_id).aggregate(
            total=Sum("value")
        )["total"]

    def get_total_settled_money_of_currency_ever_owed_to_others_for_a_room(self, *, debitor_id, currency_id, room_id):
        return self.filter(room_id=room_id, debitor_id=debitor_id, currency_id=currency_id, settled=True).aggregate(
            total=Sum("value")
        )["total"]

    def get_total_settled_money_of_currency_ever_owed_by_others_for_a_room(self, *, creditor_id, room_id, currency_id):
        return self.filter(room_id=room_id, creditor_id=creditor_id, currency_id=currency_id, settled=True).aggregate(
            total=Sum("value")
        )["total"]
