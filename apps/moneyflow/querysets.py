from django.db import models


class MoneyFlowQuerySet(models.QuerySet):
    def filter_for_room_id(self, *, room_id: int):
        return self.filter(room_id=room_id)

    def optimise_incoming_outgoing_values_for_queryset(self):
        for money_flow in self:
            money_flow.optimise_incoming_outgoing_values()
        return self
