from decimal import Decimal

from django.db.models import Q

from apps.account.models import User
from apps.core.event_loop.registry import message_registry
from apps.currency.models import Currency
from apps.debt.models import NewDebt, Debt
from apps.transaction.messages.events.transaction import TransactionCreated


@message_registry.register_event(event=TransactionCreated)
def create_or_update_debt_on_transaction_created(context: TransactionCreated.Context):
    return
    # transaction = context.transaction
    #
    # for debitor in transaction.paid_for.all():
    #     existing_unsettled_debt_qs = NewDebt.objects.filter(
    #         creditor_id=transaction.paid_by_id,
    #         debitor_id=debitor.id,
    #         currency=transaction.currency,
    #         room_id=transaction.room_id,
    #         settled=False,
    #     )
    #
    #     if not existing_unsettled_debt_qs.exists():
    #         NewDebt.objects.create(
    #             debitor=debitor,
    #             creditor=transaction.paid_by,
    #             room=transaction.room,
    #             value=transaction.value,
    #             currency=transaction.currency,
    #         )
    #         continue
    #
    #     if existing_unsettled_debt_qs.count() > 1:
    #         raise Exception(existing_unsettled_debt_qs.count())
    #
    #     if existing_unsettled_debt_qs.count() == 1:
    #         debt = existing_unsettled_debt_qs.first()
    #         debt.value += transaction.value
    #         debt.save()


@message_registry.register_event(event=TransactionCreated)
def reduce_some_sheit(context: TransactionCreated.Context):
    clean_dictionary = Debt.objects.get_debts_for_user_for_room_as_dict(context.transaction.room_id)

    created_debt_ids_tuple = ()
    touched_debt_ids_tuple = ()

    for debitor_name in clean_dictionary:
        for creditor_name in clean_dictionary[debitor_name]:
            for currency_sign in clean_dictionary[debitor_name][creditor_name]:
                value = clean_dictionary[debitor_name][creditor_name][currency_sign]

                debitor = User.objects.get(username=debitor_name)
                creditor = User.objects.get(username=creditor_name)

                debt_qs = NewDebt.objects.filter(
                    room=context.transaction.room,
                    debitor=debitor,
                    creditor=creditor,
                    currency__sign=currency_sign,
                    settled=False,
                )

                if not debt_qs.exists():
                    if value != Decimal(0):
                        created_debt_ids_tuple += (
                            NewDebt.objects.create(
                                debitor=debitor,
                                creditor=creditor,
                                room=context.transaction.room,
                                value=value,
                                currency=Currency.objects.get(sign=currency_sign),
                            ).id,
                        )
                        continue

                if debt_qs.count() == 1:
                    debt = debt_qs.first()
                    if value != Decimal(0):
                        debt.value = value
                        debt.save()
                        touched_debt_ids_tuple += (debt.id,)
                    else:
                        debt.delete()

    # Delete any untouched, unsettled debt objects
    NewDebt.objects.exclude(Q(id__in=(created_debt_ids_tuple + touched_debt_ids_tuple)) | Q(settled=True)).delete()
