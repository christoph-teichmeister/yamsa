# Hack to avoid circular imports just because I was trying to type properly
from typing import TYPE_CHECKING, Tuple

from _decimal import Decimal
from django.db import models
from django.db.models import Sum

from apps.account.models import User
from apps.moneyflow.querysets import MoneyFlowQuerySet
from apps.transaction.models import Transaction

if TYPE_CHECKING:
    from apps.moneyflow.models import MoneyFlow, MoneyFlowLog


class MoneyFlowManager(models.Manager):
    def get_queryset(self) -> MoneyFlowQuerySet:
        return MoneyFlowQuerySet(self.model, using=self._db)

    def create_or_update_flows_for_transaction(self, transaction: Transaction):
        creditor: User = transaction.paid_by

        # creditor_incoming_money_value: Decimal = Decimal(0)

        flows_to_be_created: Tuple = ()
        flows_to_be_updated: Tuple = ()

        flow_logs_to_be_handled_because_of_created_money_flows: Tuple = ()
        flow_logs_to_be_created_because_of_updated_money_flows: Tuple = ()

        for debitor in transaction.paid_for.all():
            if debitor == creditor:
                continue

            # creditor_incoming_money_value += transaction.value

            created, flow, flow_log = self.create_or_update_flow(
                is_debitor_flow=True, user=debitor, transaction=transaction
            )

            if created:
                flows_to_be_created += (flow,)
                flow_logs_to_be_handled_because_of_created_money_flows += (
                    (flow, flow_log),
                )
            else:
                flows_to_be_updated += (flow,)
                flow_logs_to_be_created_because_of_updated_money_flows += (flow_log,)

        created, flow, flow_log = self.create_or_update_flow(
            is_debitor_flow=False, user=creditor, transaction=transaction
        )

        if created:
            flows_to_be_created += (flow,)
            flow_logs_to_be_handled_because_of_created_money_flows += (
                (flow, flow_log),
            )
        else:
            flows_to_be_updated += (flow,)
            flow_logs_to_be_created_because_of_updated_money_flows += (flow_log,)

        all_flows = sorted(
            flows_to_be_created + flows_to_be_updated,
            key=lambda touched_flow: touched_flow.user_id,
        )

        for flow in all_flows:
            flow.optimise_incoming_outgoing_values()

        self.bulk_create(flows_to_be_created)
        self.bulk_update(flows_to_be_updated, fields=("outgoing", "incoming"))

        from apps.moneyflow.models import MoneyFlowLog

        MoneyFlowLog.objects.bulk_create(
            flow_logs_to_be_created_because_of_updated_money_flows
        )

        flow_logs_to_be_created_because_of_created_money_flows = ()
        for (
            flow_and_flow_log_tuple
        ) in flow_logs_to_be_handled_because_of_created_money_flows:
            money_flow = flow_and_flow_log_tuple[0]
            money_flow_log = flow_and_flow_log_tuple[1]

            money_flow_log.money_flow_id = self.model.objects.get(
                user_id=money_flow.user_id, room_id=money_flow.room_id
            ).id

            flow_logs_to_be_created_because_of_created_money_flows += (money_flow_log,)

        MoneyFlowLog.objects.bulk_create(
            flow_logs_to_be_created_because_of_created_money_flows
        )

        # print(f"\n{transaction}\n{[e for e in all_flows]}\n")

    def create_or_update_flow(
        self, *, is_debitor_flow: bool, user: User, transaction: Transaction
    ) -> tuple[bool, "MoneyFlow", "MoneyFlowLog"]:
        """DOES NOT SAVE THE FLOW, just updates its values"""
        money_field = "outgoing" if is_debitor_flow else "incoming"

        existing_money_flow_qs = self.get_queryset().filter(user_id=user.id)
        transaction_value = (
            transaction.value * (transaction.paid_for.exclude(id=user.id).count())
            if not is_debitor_flow
            else transaction.value
        )

        from apps.moneyflow.models import MoneyFlowLog

        if not existing_money_flow_qs.exists():
            money_flow = self.model(
                **{
                    "user": user,
                    "room_id": transaction.room_id,
                    f"{money_field}": transaction_value,
                }
            )
            money_flow_log = MoneyFlowLog(
                log_message=f"Money Flow for {user} created! (Transaction: {transaction})\n\n"
                f"Outgoing is: {money_flow.outgoing} {money_flow.room.preferred_currency.sign} and Incoming is:"
                f" {money_flow.incoming} {money_flow.room.preferred_currency.sign}"
            )

            return True, money_flow, money_flow_log
        else:
            existing_money_flow = existing_money_flow_qs.first()

            old_value = getattr(existing_money_flow, money_field)
            new_value = old_value + transaction_value
            setattr(existing_money_flow, money_field, new_value)

            updated_money_field_str = (
                (
                    f"Outgoing was: {old_value} {existing_money_flow.room.preferred_currency.sign} "
                    f"and now is: {new_value} {existing_money_flow.room.preferred_currency.sign}"
                )
                if is_debitor_flow
                else (
                    f"Incoming was: {old_value} {existing_money_flow.room.preferred_currency.sign} "
                    f"and now is: {new_value} {existing_money_flow.room.preferred_currency.sign}"
                )
            )
            unchanged_money_field_str = (
                (
                    f"Incoming was: {existing_money_flow.incoming} {existing_money_flow.room.preferred_currency.sign} "
                    f"and now is: {existing_money_flow.incoming} {existing_money_flow.room.preferred_currency.sign}"
                )
                if is_debitor_flow
                else (
                    f"Outgoing was: {existing_money_flow.outgoing} {existing_money_flow.room.preferred_currency.sign} "
                    f"and now is: {existing_money_flow.outgoing} {existing_money_flow.room.preferred_currency.sign}"
                )
            )

            money_flow_log = MoneyFlowLog(
                money_flow=existing_money_flow,
                log_message=f"Money Flow for {user} updated! (Transaction: {transaction})\n\n"
                f'Updated field is "{money_field}".\n\n'
                f"{updated_money_field_str}\n\n"
                f"{unchanged_money_field_str}",
            )

            return False, existing_money_flow, money_flow_log

    def try_to_resolve_flows_and_reduce_them_to_zero(self, *, room_id):
        """
        TODO CT: Comment (the old comment is not true anymore)
        This function is the first step towards trying to determine, which user pays who.

        As of now this does not work though, it does a "dumb" look-ahead and reduces flow values if it finds
        appropriate values. It does not store however, who pays whom.
        """
        from apps.moneyflow.models import MoneyFlow

        qs = self.get_queryset().filter_for_room_id(room_id=room_id)

        if not qs.exists():
            return qs

        outgoing_incoming_dict = qs.aggregate(Sum("outgoing"), Sum("incoming"))
        assert (
            outgoing_incoming_dict["outgoing__sum"]
            == outgoing_incoming_dict["incoming__sum"],
            "Something went majorly wrong if these values are not the same",
        )

        sorted_for_biggest_receiver_list = list(
            qs.order_by("-incoming").values("user__name", "outgoing", "incoming")
        )
        sorted_for_biggest_owes_list = list(
            qs.order_by("-outgoing").values("user__name", "outgoing", "incoming")
        )

        all_is_done = False

        while not all_is_done:
            biggest_ower_index = 0
            biggest_receive_entry = sorted_for_biggest_receiver_list[0]
            biggest_ower_entry = sorted_for_biggest_owes_list[biggest_ower_index]

            if biggest_ower_entry["user__name"] == biggest_receive_entry["user__name"]:
                biggest_ower_index += 1
                try:
                    biggest_ower_entry = sorted_for_biggest_owes_list[
                        biggest_ower_index
                    ]
                    biggest_ower_index = 0
                except IndexError:
                    break

            if biggest_receive_entry["incoming"] - biggest_ower_entry["outgoing"] > 0:
                if biggest_ower_entry["outgoing"] > 0:
                    print(
                        f'--- User {biggest_ower_entry["user__name"]} pays {biggest_ower_entry["outgoing"]} to'
                        f' {biggest_receive_entry["user__name"]}'
                    )

                biggest_receive_entry = {
                    **biggest_receive_entry,
                    "incoming": biggest_receive_entry["incoming"]
                    - biggest_ower_entry["outgoing"],
                }
                sorted_for_biggest_receiver_list.pop(0)
                sorted_for_biggest_owes_list.pop(0)
                sorted_for_biggest_receiver_list.append(biggest_receive_entry)

            else:
                if biggest_receive_entry["incoming"] > 0:
                    print(
                        f'--- User {biggest_ower_entry["user__name"]} pays {biggest_receive_entry["incoming"]} to'
                        f' {biggest_receive_entry["user__name"]}'
                    )

                biggest_ower_entry = {
                    **biggest_ower_entry,
                    "outgoing": biggest_ower_entry["outgoing"]
                    - biggest_receive_entry["incoming"],
                }
                sorted_for_biggest_receiver_list.pop(0)
                sorted_for_biggest_owes_list.pop(0)
                sorted_for_biggest_owes_list.append(biggest_ower_entry)

            all_is_done = len(sorted_for_biggest_receiver_list) == 0

        return qs
