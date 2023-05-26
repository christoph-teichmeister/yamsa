from django.db.models import Manager, QuerySet


class DebtManager(Manager):
    def get_debts_for_user_for_room(
        self, user_id: int, room_id: int
    ) -> QuerySet["Debt"]:
        return (
            self.filter(user_id=user_id, transaction__room_id=room_id)
            .exclude(transaction__paid_by_id=user_id)
            .order_by("transaction__paid_by")
            .values(
                "id",
                "transaction__paid_by__name",
                "transaction__value",
                "transaction__paid_by__paypal_me_link",
                "settled",
            )
        )

    def get_unsettled_debts_for_user_for_room(
        self, user_id: int, room_id: int
    ) -> QuerySet["Debt"]:
        return self.get_debts_for_user_for_room(user_id, room_id).filter(settled=False)

    def get_debts_for_user_for_room_as_dict(self, user_id: int, room_id: int) -> dict:
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

        debt_dict = {"open_debts": {}, "settled_debts": {}}
        for debt in debts_for_user_for_room:
            debt_id = debt.get("id")
            owed_to_id = debt.get("transaction__paid_by__name")
            paypal_me_link = debt.get("transaction__paid_by__paypal_me_link")
            transaction_value = debt.get("transaction__value")
            settled = debt.get("settled")

            key = "settled_debts" if settled else "open_debts"
            sub_dict = debt_dict[key]

            if sub_dict.get(owed_to_id) is None:
                sub_dict[owed_to_id] = {
                    "amount_owed": transaction_value,
                    "debt_ids": (debt_id,),
                    "debt_ids_as_string": f"{debt_id}",
                    "settled": True & settled,
                    "paypal_me_link": paypal_me_link,
                }
            else:
                sub_dict[owed_to_id]["amount_owed"] += transaction_value
                sub_dict[owed_to_id]["debt_ids"] += (debt_id,)
                sub_dict[owed_to_id]["debt_ids_as_string"] += f"-{debt_id}"
                sub_dict[owed_to_id]["settled"] = (
                    sub_dict[owed_to_id]["settled"] & settled
                )

        return debt_dict
