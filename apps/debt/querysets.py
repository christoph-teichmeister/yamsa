from django.db import models

from apps.account.models import User


class DebtQuerySet(models.QuerySet):
    def filter_for_room_id(self, *, room_id: int):
        return self.filter(room_id=room_id)

    def filter_for_creditor(self, *, creditor: User):
        return self.filter(creditor=creditor)

    def filter_for_debitor(self, *, debitor: User):
        return self.filter(debitor=debitor)
