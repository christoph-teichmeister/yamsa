from apps.account.models import User
from apps.core.event_loop.registry import message_registry
from apps.core.utils import add_or_update_dict
from apps.currency.models import Currency
from apps.debt.models import NewDebt
from apps.transaction.messages.events.transaction import TransactionCreated
from apps.transaction.models import Transaction


@message_registry.register_event(event=TransactionCreated)
def create_or_update_debt_on_transaction_created(context: TransactionCreated.Context):
    return
    transaction = context.transaction

    for debitor in transaction.paid_for.all():
        existing_unsettled_debt_qs = NewDebt.objects.filter(
            creditor_id=transaction.paid_by_id,
            debitor_id=debitor.id,
            currency=transaction.currency,
            room_id=transaction.room_id,
            settled=False,
        )

        if not existing_unsettled_debt_qs.exists():
            NewDebt.objects.create(
                debitor=debitor,
                creditor=transaction.paid_by,
                room=transaction.room,
                value=transaction.value,
                currency=transaction.currency,
            )
            continue

        if existing_unsettled_debt_qs.count() > 1:
            raise Exception(existing_unsettled_debt_qs.count())

        if existing_unsettled_debt_qs.count() == 1:
            debt = existing_unsettled_debt_qs.first()
            debt.value += transaction.value
            debt.save()


@message_registry.register_event(event=TransactionCreated)
def reduce_some_sheit(context: TransactionCreated.Context):
    def _get_cleaned_debt_dict(all_debts_of_room_tuple: tuple):
        cleaned_debts_dict = {}
        for debt_entry in all_debts_of_room_tuple:
            value = debt_entry[0]
            currency_sign = debt_entry[1]
            paid_by_name = debt_entry[2]
            paid_for_name = debt_entry[3]

            # If the currency is already in cleaned_debts_dict...
            if cleaned_debts_dict.get(currency_sign) is not None:
                currency_entry = cleaned_debts_dict[currency_sign]

                # If that currency already has an entry for the paid_by user...
                if currency_entry.get(paid_by_name) is not None:
                    # Update that entry with the new value
                    existing_value = currency_entry[paid_by_name]
                    cleaned_debts_dict[currency_sign][paid_by_name] = existing_value + value
                else:
                    # If the currency_sign has no entry for the user, but already exists in the dict, then it must be
                    # for another user, so we just update the entry
                    cleaned_debts_dict[currency_sign] = {**currency_entry, paid_by_name: value}

            else:
                # If the currency is not in the dict yet, create a new entry
                cleaned_debts_dict[currency_sign] = {paid_by_name: value}

            # If currency_sign is not already in the cleaned_debts_dict...
            if cleaned_debts_dict.get(currency_sign) is not None:
                currency_entry = cleaned_debts_dict[currency_sign]

                # If that currency already has an entry for the paid_for user...
                if currency_entry.get(paid_for_name) is not None:
                    # Update that entry with the new value
                    existing_value = currency_entry[paid_for_name]
                    cleaned_debts_dict[currency_sign][paid_for_name] = existing_value - value
                else:
                    # If the currency_sign has no entry for the user, but already exists in the dict, then it must be
                    # for another user, so we just update the entry
                    cleaned_debts_dict[currency_sign] = {**currency_entry, paid_for_name: 0 - value}

            else:
                # If the currency_sign is not in the dict yet, create a new entry
                cleaned_debts_dict[currency_sign] = {paid_for_name: 0 - value}
        return cleaned_debts_dict

    def _get_sorted_cleaned_creditor_debts_dict(cleaned_debts_dict):
        sorted_cleaned_creditor_debts_dict = {}
        for currency_tuple in cleaned_debts_dict.items():
            sorted_cleaned_creditor_debts_dict[currency_tuple[0]] = list(
                sorted(
                    currency_tuple[1].items(),
                    key=lambda entry: entry[1],
                )
            )
        return sorted_cleaned_creditor_debts_dict

    all_debts_of_room_tuple = tuple(
        Transaction.objects.filter(room_id=context.transaction.room_id)
        .order_by("value", "currency__sign")
        .values_list("value", "currency__sign", "paid_by__name", "paid_for__name")
    )

    if len(all_debts_of_room_tuple) == 0:
        return {}

    cleaned_debts_dict = _get_cleaned_debt_dict(all_debts_of_room_tuple)
    sorted_cleaned_creditor_debts_dict = _get_sorted_cleaned_creditor_debts_dict(cleaned_debts_dict)

    test = {}

    a_log_list = []
    for currency_sign in sorted_cleaned_creditor_debts_dict:
        all_is_done = False
        while not all_is_done:
            sorted_cleaned_creditor_debts_list = sorted_cleaned_creditor_debts_dict[currency_sign]
            cheapest_user_tuple = sorted_cleaned_creditor_debts_list[0]
            most_expensive_user_tuple = sorted_cleaned_creditor_debts_list[-1]

            diff_expensive_to_min = abs(most_expensive_user_tuple[1]) - abs(cheapest_user_tuple[1])
            if diff_expensive_to_min >= 0:
                a_log_list.append(
                    f"{cheapest_user_tuple[0]} pays {abs(cheapest_user_tuple[1])}{currency_sign} to {most_expensive_user_tuple[0]}"
                )
                add_or_update_dict(
                    dictionary=test,
                    update_value={
                        cheapest_user_tuple[0]: {
                            most_expensive_user_tuple[0]: {
                                currency_sign: abs(cheapest_user_tuple[1]),
                            }
                        }
                    },
                )

                most_expensive_user_tuple = (most_expensive_user_tuple[0], diff_expensive_to_min)

                sorted_cleaned_creditor_debts_list.pop(0)
                sorted_cleaned_creditor_debts_list.pop(-1)
                sorted_cleaned_creditor_debts_list.append(most_expensive_user_tuple)
            else:
                a_log_list.append(
                    f"{cheapest_user_tuple[0]} pays {abs(diff_expensive_to_min)}{currency_sign} to {most_expensive_user_tuple[0]}"
                )
                add_or_update_dict(
                    dictionary=test,
                    update_value={
                        cheapest_user_tuple[0]: {
                            most_expensive_user_tuple[0]: {
                                currency_sign: abs(diff_expensive_to_min),
                            }
                        }
                    },
                )

                cheapest_user_tuple = (cheapest_user_tuple[0], cheapest_user_tuple[1] - diff_expensive_to_min)

                sorted_cleaned_creditor_debts_list.pop(0)
                sorted_cleaned_creditor_debts_list.pop(-1)
                sorted_cleaned_creditor_debts_list.append(cheapest_user_tuple)

            sorted_cleaned_creditor_debts_list = list(
                sorted(sorted_cleaned_creditor_debts_list, key=lambda entry: entry[1])
            )

            all_is_done = len(sorted_cleaned_creditor_debts_list) == 1

    for debitor_name in test:
        for creditor_name in test[debitor_name]:
            for currency_sign in test[debitor_name][creditor_name]:
                value = test[debitor_name][creditor_name][currency_sign]

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
                    NewDebt.objects.create(
                        debitor=debitor,
                        creditor=creditor,
                        room=context.transaction.room,
                        value=value,
                        currency=Currency.objects.get(sign=currency_sign),
                    )
                    continue

                if debt_qs.count() == 1:
                    debt = debt_qs.first()
                    debt.value += value
