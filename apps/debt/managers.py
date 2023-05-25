from django.db.models import Manager, QuerySet


class DebtManager(Manager):
    def get_debts_for_user_for_room(
        self, user_id: int, room_id: int
    ) -> QuerySet["Debt"]:
        return (
            self.filter(user_id=user_id, transaction__room_id=room_id)
            .exclude(transaction__paid_by_id=user_id)
            .order_by("transaction__paid_by")
            .values("id", "transaction__paid_by__name", "transaction__value", "settled")
        )

    def get_debts_for_user_for_room_as_dict(self, user_id: int, room_id: int) -> dict:
        """
        Exemplary return:
            {
            'yamsa-admin': {
                'amount_owed': Decimal('36.59'),
                'debt_ids': (25, 22, 3),
                'debt_ids_as_string': '25-22-3',
                'settled': False
                },
            'non_guest_user_1': {
                'amount_owed': Decimal('30.00'),
                'debt_ids': (20,),
                'debt_ids_as_string': '20',
                'settled': False
                },
            'guest_user_2': {
                'amount_owed': Decimal('26.00'),
                'debt_ids': (33, 9),
                'debt_ids_as_string': '33-9',
                'settled': False
                }
            }
        """

        debts_for_user_for_room = self.get_debts_for_user_for_room(user_id, room_id)

        debt_dict = {}
        for debt in debts_for_user_for_room:
            debt_id = debt.get("id")
            owed_to_id = debt.get("transaction__paid_by__name")
            transaction_value = debt.get("transaction__value")
            settled = debt.get("settled")

            if debt_dict.get(owed_to_id) is None:
                debt_dict[owed_to_id] = {
                    "amount_owed": transaction_value,
                    "debt_ids": (debt_id,),
                    "debt_ids_as_string": f"{debt_id}",
                    "settled": True & settled,
                }
            else:
                debt_dict[owed_to_id]["amount_owed"] += transaction_value
                debt_dict[owed_to_id]["debt_ids"] += (debt_id,)
                debt_dict[owed_to_id]["debt_ids_as_string"] += f"-{debt_id}"
                debt_dict[owed_to_id]["settled"] = (
                    debt_dict[owed_to_id]["settled"] & settled
                )

        return debt_dict
