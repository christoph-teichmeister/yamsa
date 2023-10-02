from django.db.models import Manager, QuerySet


class DebtManager(Manager):
    def get_debts_for_user_for_room(self, user_id: int, room_id: int) -> QuerySet[dict]:
        return (
            self.filter(user_id=user_id, transaction__room_id=room_id)
            .select_related(
                "transaction", "transaction__paid_by", "transaction__currency"
            )
            .exclude(transaction__paid_by_id=user_id)
            .order_by("transaction__paid_by")
            .values(
                "id",
                "transaction__paid_by__name",
                "transaction__currency__sign",
                "transaction__value",
                "transaction__paid_by__paypal_me_link",
                "settled",
            )
        )

    def get_unsettled_debts_for_user_for_room(
        self, user_id: int, room_id: int
    ) -> QuerySet[dict]:
        return self.get_debts_for_user_for_room(user_id, room_id).filter(settled=False)

    def _get_cleaned_debt_dict(self, all_debts_of_room_tuple: tuple):
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


    def _get_sorted_cleaned_creditor_debts_dict(self, cleaned_debts_dict):
        sorted_cleaned_creditor_debts_dict = {}
        for currency_tuple in cleaned_debts_dict.items():
            sorted_cleaned_creditor_debts_dict[currency_tuple[0]]= list(
                sorted(
                    currency_tuple[1].items(),
                    key=lambda entry: entry[1],
                )
            )
        return sorted_cleaned_creditor_debts_dict



    def get_debts_for_user_for_room_as_dict(self, room_id: int) -> list:
        # TODO CT: Work on this
        all_debts_of_room_tuple = tuple(
            self.filter(transaction__room_id=room_id)
            .order_by("transaction__value", "transaction__currency__sign")
            .values_list("transaction__value", "transaction__currency__sign", "transaction__paid_by__name",
                         "user__name")
        )

        if len(all_debts_of_room_tuple) == 0:
            return []

        cleaned_debts_dict = self._get_cleaned_debt_dict(all_debts_of_room_tuple)
        sorted_cleaned_creditor_debts_dict = self._get_sorted_cleaned_creditor_debts_dict(cleaned_debts_dict)

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
                    most_expensive_user_tuple = (most_expensive_user_tuple[0], diff_expensive_to_min)

                    sorted_cleaned_creditor_debts_list.pop(0)
                    sorted_cleaned_creditor_debts_list.pop(-1)
                    sorted_cleaned_creditor_debts_list.append(most_expensive_user_tuple)
                else:
                    a_log_list.append(
                        f"{cheapest_user_tuple[0]} pays {abs(diff_expensive_to_min)}{currency_sign} to {most_expensive_user_tuple[0]}"
                    )
                    cheapest_user_tuple = (cheapest_user_tuple[0], cheapest_user_tuple[1] - diff_expensive_to_min)

                    sorted_cleaned_creditor_debts_list.pop(0)
                    sorted_cleaned_creditor_debts_list.pop(-1)
                    sorted_cleaned_creditor_debts_list.append(cheapest_user_tuple)

                sorted_cleaned_creditor_debts_list = list(
                    sorted(sorted_cleaned_creditor_debts_list, key=lambda entry: entry[1])
                )

                all_is_done = len(sorted_cleaned_creditor_debts_list) == 1

        return a_log_list

    def get_debts_for_user_for_room_as_dict_old(
        self, user_id: int, room_id: int
    ) -> dict:
        """
        Exemplary return:
            {
                'open_debts': {
                    'yamsa-admin': {
                        'amount_owed': Decimal('36.59'),
                        'debt_ids': (25, 22, 3),
                        'debt_ids_as_string': '25-22-3',
                        'settled': False,
                        'paypal_me_link': "<A PayPal.me URL>"
                    },
                    'non_guest_user_1': {
                        'amount_owed': Decimal('30.00'),
                        'debt_ids': (20,),
                        'debt_ids_as_string': '20',
                        'settled': False,
                        'paypal_me_link': "<A PayPal.me URL>"
                    },
                },
                'settled_debts': {
                    'guest_user_2': {
                        'amount_owed': Decimal('26.00'),
                        'debt_ids': (33, 9),
                        'debt_ids_as_string': '33-9',
                        'settled': False,
                        'paypal_me_link': "<A PayPal.me URL>"
                    }
                }
            }
        """

        debts_for_user_for_room = self.get_debts_for_user_for_room(user_id, room_id)

        if not debts_for_user_for_room.exists():
            return {}

        debt_dict = {"open_debts": {}, "settled_debts": {}}
        for debt in debts_for_user_for_room:
            debt_id = debt.get("id")
            owed_to_id = debt.get("transaction__paid_by__name")
            paypal_me_link = debt.get("transaction__paid_by__paypal_me_link")
            transaction_value = debt.get("transaction__value")
            currency_sign = debt.get("transaction__currency__sign")
            settled = debt.get("settled")

            key = "settled_debts" if settled else "open_debts"
            sub_dict = debt_dict[key]

            if sub_dict.get(owed_to_id) is None:
                sub_dict[owed_to_id] = {
                    "amount_owed": {f"{currency_sign}": transaction_value},
                    "debt_ids": (debt_id,),
                    "debt_ids_as_string": f"{debt_id}",
                    "settled": True & settled,
                    "paypal_me_link": paypal_me_link,
                }
            else:
                if sub_dict[owed_to_id]["amount_owed"].get(currency_sign) is not None:
                    sub_dict[owed_to_id]["amount_owed"][
                        currency_sign
                    ] += transaction_value
                else:
                    sub_dict[owed_to_id]["amount_owed"][
                        currency_sign
                    ] = transaction_value

                sub_dict[owed_to_id]["debt_ids"] += (debt_id,)
                sub_dict[owed_to_id]["debt_ids_as_string"] += f"-{debt_id}"
                sub_dict[owed_to_id]["settled"] = (
                    sub_dict[owed_to_id]["settled"] & settled
                )

        return debt_dict


class NewDebtManager(Manager):
    def get_queryset(self) -> NewDebtQuerySet:
        return NewDebtQuerySet(self.model, using=self._db)
