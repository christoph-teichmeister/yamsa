from django.db.models import QuerySet

from apps.transaction.dataclasses import Debt, DebtTuple, MoneyFlow, MoneyFlowTuple
from apps.transaction.models import Transaction


class DebtService:
    @staticmethod
    def get_debts_dict(room_transactions_qs: QuerySet[Transaction]) -> dict:
        debts = {}

        for transaction in room_transactions_qs:
            for debitor in transaction.paid_for.all():
                paid_for_name = debitor.name
                paid_by_name = transaction.paid_by.name
                value = transaction.value

                if paid_for_name == paid_by_name:
                    continue

                try:
                    debts[paid_for_name][paid_by_name] += value
                except KeyError:
                    try:
                        debts[paid_for_name][paid_by_name] = value
                    except KeyError:
                        debts[paid_for_name] = {paid_by_name: value}

        return debts

    @staticmethod
    def build_money_flow_tuple(queryset: QuerySet[Transaction]) -> MoneyFlowTuple:
        debt_tuple: DebtTuple = DebtTuple()

        # Create a debt_tuple consisting of ALL debts
        for transaction in queryset:
            creditor = transaction.paid_by

            for debitor in transaction.paid_for.all():
                # Find existing exact connection (A owes B from at least TWO transactions)
                existing_connection_qs = debt_tuple.filter(deb_cred=(debitor, creditor))
                existing_connection = existing_connection_qs.first()

                if existing_connection:
                    debt_tuple.update_debt(
                        existing_connection, amount_owed__add=transaction.value
                    )
                else:
                    if debitor != creditor:
                        debt_tuple.add_item(
                            Debt(
                                debitor=debitor,
                                creditor=creditor,
                                amount_owed=transaction.value,
                            )
                        )
                    else:
                        print(f"Debitor was about to be his own Creditor {debitor=}")

        money_flow_tuple: MoneyFlowTuple = MoneyFlowTuple()

        # Create a dict of how many each person pays and receives
        for debt in debt_tuple:
            existing_debitor_flow_qs = money_flow_tuple.filter(user=debt.debitor)
            existing_debitor_flow = existing_debitor_flow_qs.first()

            if existing_debitor_flow:
                money_flow_tuple.update_debt(
                    existing_debitor_flow, outgoing__add=debt.amount_owed
                )
            else:
                money_flow_tuple.add_item(
                    MoneyFlow(user=debt.debitor, outgoing=debt.amount_owed)
                )

            existing_creditor_flow_qs = money_flow_tuple.filter(user=debt.creditor)
            existing_creditor_flow = existing_creditor_flow_qs.first()

            if existing_creditor_flow:
                money_flow_tuple.update_debt(
                    existing_creditor_flow, incoming__add=debt.amount_owed
                )
            else:
                money_flow_tuple.add_item(
                    MoneyFlow(user=debt.creditor, incoming=debt.amount_owed)
                )

        print("\nFLOWS BEFORE OPTIMISING:\n")
        money_flow_tuple.print_items()

        [flow.optimise_flows() for flow in money_flow_tuple]

        print("\nFLOWS AFTER OPTIMISING:\n")
        money_flow_tuple.print_items()

        return money_flow_tuple
