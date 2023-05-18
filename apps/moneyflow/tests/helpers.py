from _decimal import Decimal

from apps.account.models import User


class MoneyFlowHelpersMixin:
    def assert_money_flow_values(
            self,
            *,
            user: User,
            incoming: int | float,
            outgoing: int | float,
    ):
        user_money_flow = user.money_flows.first()
        self.assertEqual(user_money_flow.incoming, round(Decimal(incoming), 2))
        self.assertEqual(user_money_flow.outgoing, round(Decimal(outgoing), 2))
