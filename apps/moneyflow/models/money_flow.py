from _decimal import Decimal

from ai_django_core.models import CommonInfo
from django.db import models

from apps.moneyflow.managers import MoneyFlowManager


class MoneyFlow(CommonInfo):
    user = models.ForeignKey("account.User", on_delete=models.CASCADE)
    room = models.ForeignKey("room.Room", on_delete=models.CASCADE)

    outgoing = models.DecimalField(
        "Outgoing Money", max_digits=10, decimal_places=2, default=Decimal(0)
    )
    incoming = models.DecimalField(
        "Incoming Money", max_digits=10, decimal_places=2, default=Decimal(0)
    )

    objects = MoneyFlowManager()

    class Meta:
        verbose_name = "Money Flow"
        verbose_name_plural = "Money Flows"
        default_related_name = "money_flows"
        unique_together = (
            "user",
            "room",
        )

    def optimise_incoming_outgoing_values(self):
        if self.outgoing > self.incoming:
            self.outgoing = self.outgoing - self.incoming
            self.incoming = Decimal(0)

        elif self.outgoing < self.incoming:
            self.incoming = self.incoming - self.outgoing
            self.outgoing = Decimal(0)

        else:
            self.incoming = Decimal(0)
            self.outgoing = Decimal(0)

    def __str__(self):
        return f"{self.user} - Out: {self.outgoing}€ | In: {self.incoming}€"
