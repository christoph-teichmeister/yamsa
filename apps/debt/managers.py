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

    def get_debts_for_user_for_room_as_dict(self, room_id: int) -> list:
        # TODO CT: Work on this
        all_debts_of_room_tuple = tuple(
            self.filter(transaction__room_id=room_id)
            .order_by("transaction__value")
            .values_list("transaction__value", "transaction__currency__sign", "transaction__paid_by__name",
                         "user__name")
        )

        if len(all_debts_of_room_tuple) == 0:
            return []

        cleaned_debts_dict = {}
        for debt_entry in all_debts_of_room_tuple:
            value = debt_entry[0]
            currency_sign = debt_entry[1]
            paid_by_name = debt_entry[2]
            paid_for_name = debt_entry[3]

            if cleaned_debts_dict.get(paid_by_name, None) is not None:
                cleaned_debts_dict[paid_by_name] = (cleaned_debts_dict[paid_by_name][0] + value,
                                                       cleaned_debts_dict[paid_by_name][1])
            else:
                cleaned_debts_dict[paid_by_name] = (value, currency_sign)

            if cleaned_debts_dict.get(paid_for_name, None) is not None:
                cleaned_debts_dict[paid_for_name] = (cleaned_debts_dict[paid_for_name][0] - value,
                                                        cleaned_debts_dict[paid_for_name][1])
            else:
                cleaned_debts_dict[paid_for_name] = (0 - value, currency_sign)

        sorted_cleaned_creditor_debts_list = list(
            sorted(
                cleaned_debts_dict.items(),
                key=lambda entry: entry[1],
            )
        )

        a_log_list = []

        all_is_done = False
        while not all_is_done:
            cheapest_tuple = sorted_cleaned_creditor_debts_list[0]
            most_expensive_tuple = sorted_cleaned_creditor_debts_list[-1]

            diff_expensive_to_min = abs(most_expensive_tuple[1][0]) - abs(cheapest_tuple[1][0])
            if diff_expensive_to_min >= 0:
                a_log_list.append(
                    f"{cheapest_tuple[0]} pays {abs(cheapest_tuple[1][0])}{cheapest_tuple[1][1]} to {most_expensive_tuple[0]}"
                )
                most_expensive_tuple = (most_expensive_tuple[0], (diff_expensive_to_min, most_expensive_tuple[1][1]))
                sorted_cleaned_creditor_debts_list.pop(0)
                sorted_cleaned_creditor_debts_list.pop(-1)
                sorted_cleaned_creditor_debts_list.append(most_expensive_tuple)
            else:
                a_log_list.append(
                    f"{cheapest_tuple[0]} pays {abs(diff_expensive_to_min)}{cheapest_tuple[1][1]} to {most_expensive_tuple[0]}"
                )
                cheapest_tuple = (cheapest_tuple[0], (cheapest_tuple[1][0] - diff_expensive_to_min, cheapest_tuple[1][
                    1]))
                sorted_cleaned_creditor_debts_list.pop(0)
                sorted_cleaned_creditor_debts_list.pop(-1)
                sorted_cleaned_creditor_debts_list.append(cheapest_tuple)

            sorted_cleaned_creditor_debts_list = list(
                sorted(sorted_cleaned_creditor_debts_list, key=lambda entry: entry[1])
            )

            all_is_done = len(sorted_cleaned_creditor_debts_list) == 1

        # print(a_log_list)
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
