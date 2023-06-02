from django.db.models import Manager, QuerySet


class DebtManager(Manager):
    def get_debts_for_user_for_room(
        self, user_id: int, room_id: int
    ) -> QuerySet["Debt"]:
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
    ) -> QuerySet["Debt"]:
        return self.get_debts_for_user_for_room(user_id, room_id).filter(settled=False)

    def get_debts_for_user_for_room_as_dict(self, room_id: int) -> dict:
        # TODO CT: Work on this
        alL_debts_of_room_tuple = tuple(
            self.filter(transaction__room_id=room_id)
            .order_by("transaction__value")
            .values_list("transaction__value", "transaction__paid_by")
        )

        cleaned_debt_entry_dict = {}
        for debt_entry in alL_debts_of_room_tuple:
            value = debt_entry[0]
            paid_by_id = debt_entry[1]

            if cleaned_debt_entry_dict.get(paid_by_id, None) is not None:
                cleaned_debt_entry_dict[paid_by_id] += value
            else:
                cleaned_debt_entry_dict[paid_by_id] = value

        sorted_debt_entry_list = list(
            sorted(
                cleaned_debt_entry_dict.items(),
                key=lambda entry: entry[1],
            )
        )

        if len(sorted_debt_entry_list) == 0:
            return {}

        cheapest_user_id = sorted_debt_entry_list[0][0]
        most_expensive_user_id = sorted_debt_entry_list[-1][0]

        all_is_done = False
        while not all_is_done:
            cheapest = sorted_debt_entry_list[0]
            most_expensive = sorted_debt_entry_list[-1]

            if most_expensive[1] - cheapest[1] > 0:
                most_expensive = (most_expensive[0], most_expensive[1] - cheapest[1])
                sorted_debt_entry_list.pop(0)
                sorted_debt_entry_list.pop(-1)
                sorted_debt_entry_list.append(most_expensive)

            sorted_debt_entry_list = list(
                sorted(sorted_debt_entry_list, key=lambda entry: entry[1])
            )

            all_is_done = len(sorted_debt_entry_list) == 1

        print(
            f"{cheapest_user_id} pays {sorted_debt_entry_list[0][1]} to {most_expensive_user_id}"
        )

        return {}

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
