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


@message_registry.register_event(event=TransactionCreated)
def reduce_some_sheit(context: TransactionCreated.Context):
    all_debts_of_room_tuple = tuple(
        Debt.objects.filter(transaction__room_id=context.transaction.room_id)
        .order_by("transaction__value", "transaction__currency__sign")
        .values_list("user__name", "transaction__paid_by__name", "transaction__value")
    )

    ret = simplify_debts(all_debts_of_room_tuple)
    print(ret)


def simplify_debts(debts):
    # Create a dictionary to track how much each person owes or is owed
    balances = {}

    # Populate the balances dictionary based on the provided debts
    for debtor, creditor, amount in debts:
        balances[debtor] = balances.get(debtor, 0) - amount
        balances[creditor] = balances.get(creditor, 0) + amount

    # Initialize two lists for debtors and creditors
    debtors = []
    creditors = []

    # Separate debtors and creditors, ignoring those with a balance of 0
    for person, balance in balances.items():
        if balance < 0:
            debtors.append((person, balance))
        elif balance > 0:
            creditors.append((person, balance))

    # Sort debtors and creditors based on the owed amounts
    debtors.sort(key=lambda x: x[1])
    creditors.sort(key=lambda x: x[1], reverse=True)

    # Initialize a list to track the transactions
    transactions = []

    # Perform debt consolidation
    while debtors and creditors:
        debtor, debt = debtors[0]
        creditor, credit = creditors[0]

        # Calculate the amount to transfer
        transfer_amount = min(-debt, credit)

        # Update balances and create a transaction
        balances[debtor] += transfer_amount
        balances[creditor] -= transfer_amount

        # Add the transaction to the list
        transactions.append((debtor, creditor, transfer_amount))

        # Remove debtors and creditors with zero balance
        if balances[debtor] == 0:
            debtors.pop(0)
        if balances[creditor] == 0:
            creditors.pop(0)

    return transactions
