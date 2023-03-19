from typing import Tuple

from _decimal import Decimal
from django.db import models
from django.db.models import Sum

from apps.account.models import User
from apps.moneyflow.querysets import MoneyFlowQuerySet
from apps.transaction.models import Transaction


class MoneyFlowManager(models.Manager):
    def get_queryset(self) -> MoneyFlowQuerySet:
        return MoneyFlowQuerySet(self.model, using=self._db)

    def create_or_update_flows_for_transaction(self, transaction: Transaction):
        creditor: User = transaction.paid_by

        creditor_incoming_money_value: Decimal = Decimal(0)

        flows_to_be_created: Tuple = ()
        flows_to_be_updated: Tuple = ()

        for debitor in transaction.paid_for.all():
            if debitor == creditor:
                continue

            creditor_incoming_money_value += transaction.value

            created, flow = self.create_or_update_flow(
                is_debitor_flow=True, user=debitor, transaction=transaction
            )

            if created:
                flows_to_be_created += (flow,)
            else:
                flows_to_be_updated += (flow,)

        created, flow = self.create_or_update_flow(
            is_debitor_flow=False, user=creditor, transaction=transaction
        )
        if created:
            flows_to_be_created += (flow,)
        else:
            flows_to_be_updated += (flow,)

        self.bulk_create(flows_to_be_created)
        self.bulk_update(flows_to_be_updated, fields=("outgoing", "incoming"))

        # print(
        #     f"\n{transaction}\n{[e for e in flows_to_be_created + flows_to_be_updated]}\n"
        # )

    def create_or_update_flow(
        self, *, is_debitor_flow: bool, user: User, transaction: Transaction
    ):
        """DOES NOT SAVE THE FLOW, just updates its values"""
        money_field = "outgoing" if is_debitor_flow else "incoming"

        existing_money_flow_qs = self.get_queryset().filter(user_id=user.id)

        if not existing_money_flow_qs.exists():
            return True, self.model(
                **{
                    "user": user,
                    "room_id": transaction.room_id,
                    f"{money_field}": transaction.value,
                }
            )
        else:
            existing_money_flow = existing_money_flow_qs.first()

            old_value = getattr(existing_money_flow, money_field)
            setattr(existing_money_flow, money_field, old_value + transaction.value)
            return False, existing_money_flow

    def try_to_resolve_flows_and_reduce_them_to_zero(self, *, room_id):
        """
        This function is the first step towards trying to determine, which user pays who.

        As of now this does not work though, it does a "dumb" look-ahead and reduces flow values if it finds
        appropriate values. It does not store however, who pays whom.
        """
        from apps.moneyflow.models import MoneyFlow

        qs = self.get_queryset().filter_for_room_id(room_id=room_id)

        outgoing_incoming_dict = qs.aggregate(Sum("outgoing"), Sum("incoming"))
        assert (
            outgoing_incoming_dict["outgoing__sum"]
            == outgoing_incoming_dict["incoming__sum"],
            "Something went majorly wrong if these values are not the same",
        )

        for index, flow in enumerate(qs):
            if index == qs.count() - 1:
                break

            first_flow: MoneyFlow = flow
            second_flow: MoneyFlow = qs[index + 1]

            if first_flow.outgoing > second_flow.incoming:
                first_flow.outgoing -= second_flow.incoming
                second_flow.incoming = Decimal(0)

            elif first_flow.outgoing < second_flow.incoming:
                second_flow.incoming -= first_flow.outgoing
                first_flow.outgoing = Decimal(0)

            elif first_flow.incoming > second_flow.outgoing:
                first_flow.incoming -= second_flow.outgoing
                second_flow.outgoing = Decimal(0)

            elif first_flow.incoming < second_flow.outgoing:
                second_flow.outgoing -= first_flow.incoming
                first_flow.incoming = Decimal(0)

        qs.bulk_update(qs, ("incoming", "outgoing"))

        return qs
