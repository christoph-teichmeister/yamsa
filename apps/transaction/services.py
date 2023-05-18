from django.db.models import QuerySet

from apps.transaction.models import Transaction


class DebtService:
    @staticmethod
    def get_debts_dict(room_transactions_qs: QuerySet[Transaction]) -> dict:
        debts = {}

        for transaction in room_transactions_qs:
            for debitor in transaction.paid_for.all():
                paid_for_name = debitor.name
                paid_by_name = transaction.paid_by.name
                value = transaction.value

                if paid_for_name == paid_by_name:
                    continue

                try:
                    debts[paid_for_name][paid_by_name]["value"] += value
                except KeyError:
                    try:
                        debts[paid_for_name][paid_by_name]["value"] = value
                    except KeyError:
                        debts[paid_for_name] = {
                            paid_by_name: {"value": value, "transaction": transaction}
                        }

        return debts
