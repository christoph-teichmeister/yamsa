from ambient_toolbox.models import CommonInfo
from django.db import models


class MoneyFlowLog(CommonInfo):
    money_flow = models.ForeignKey("moneyflow.MoneyFlow", on_delete=models.CASCADE)
    log_message = models.TextField(max_length=5000)

    class Meta:
        verbose_name = "Money Flow Log"
        verbose_name_plural = "Money Flow Logs"
        default_related_name = "money_flow_logs"

    def __str__(self):
        return f"{self.id}: Money Flow Log for {self.money_flow}"
