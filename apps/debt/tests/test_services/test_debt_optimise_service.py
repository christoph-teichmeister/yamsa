from decimal import Decimal

import pytest

from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.debt.models import Debt
from apps.debt.services.debt_optimise_service import DebtOptimiseService
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation


@pytest.mark.django_db
class TestDebtOptimiseService:
    def test_aggregated_balances_include_settled_debts_across_currencies(self, room, user, guest_user):
        other_user = UserFactory()
        room.users.add(other_user)

        currency_1 = CurrencyFactory()
        currency_2 = CurrencyFactory()
        currency_ids = (currency_1.id, currency_2.id)

        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user, other_user),
            parent_transaction_kwargs={"currency": currency_1},
            child_transaction_kwargs={"value": Decimal("10")},
        )
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=guest_user,
            paid_for_tuple=(user, other_user),
            parent_transaction_kwargs={"currency": currency_2},
            child_transaction_kwargs={"value": Decimal("7")},
        )

        settled_debt = room.debts.get(
            creditor_id=user.id,
            debitor_id=guest_user.id,
            currency_id=currency_1.id,
            settled=False,
        )
        settled_debt.settled = True
        settled_debt.save()

        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=other_user,
            paid_for_tuple=(guest_user, user),
            parent_transaction_kwargs={"currency": currency_1},
            child_transaction_kwargs={"value": Decimal("5")},
        )

        unsettled_snapshot = list(
            room.debts.filter(settled=False)
            .values_list("debitor_id", "creditor_id", "currency_id", "value")
            .order_by("currency_id", "debitor_id", "creditor_id")
        )

        DebtOptimiseService.process(room_id=room.id)

        reprocessed_snapshot = list(
            room.debts.filter(settled=False)
            .values_list("debitor_id", "creditor_id", "currency_id", "value")
            .order_by("currency_id", "debitor_id", "creditor_id")
        )

        expected_debts = [
            (guest_user.id, user.id, currency_1.id, Decimal("5")),
            (other_user.id, guest_user.id, currency_2.id, Decimal("7")),
            (user.id, guest_user.id, currency_2.id, Decimal("7")),
        ]

        def ordering_key(debt):
            return debt[2], debt[0], debt[1]

        sorted_expected = sorted(expected_debts, key=ordering_key)
        assert unsettled_snapshot == sorted_expected
        assert reprocessed_snapshot == sorted_expected
        assert room.debts.filter(settled=True).filter(
            debitor_id=guest_user.id, creditor_id=user.id, value=Decimal("10")
        ).exists()
        assert len({currency_id for _, _, currency_id, _ in unsettled_snapshot}) == len(currency_ids)

        assert Debt.objects.filter(creditor=user, debitor=guest_user, currency=currency_1, settled=True).exists()
