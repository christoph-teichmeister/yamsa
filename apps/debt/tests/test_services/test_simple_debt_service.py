from decimal import Decimal

import pytest

from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.debt.services.simple_debt_service import SimpleDebtService
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


class TestSimpleDebtService:
    def test_returns_no_rows_without_transactions(self, room, user):
        assert SimpleDebtService.get_rows(room_id=room.id, viewer_id=user.id) == []

    def test_row_points_from_the_covered_user_to_the_payer(self, room, user, guest_user):
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))

        rows = SimpleDebtService.get_rows(room_id=room.id, viewer_id=user.id)

        assert len(rows) == 1
        row = rows[0]
        assert row.debitor == guest_user
        assert row.creditor == user
        assert row.value == Decimal("13")
        assert row.settled is False
        assert row.viewer_is_debitor is False
        assert row.viewer_is_creditor is True

    def test_shares_the_payer_covered_for_themselves_are_no_debt(self, room, user, guest_user):
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(user, guest_user))

        rows = SimpleDebtService.get_rows(room_id=room.id, viewer_id=user.id)

        assert len(rows) == 1
        assert rows[0].debitor == guest_user

    def test_amounts_of_the_same_pair_are_summed_within_a_currency(self, room, user, guest_user):
        currency = CurrencyFactory()
        for _ in range(2):
            create_parent_transaction_with_optimisation(
                room=room,
                paid_by=user,
                paid_for_tuple=(guest_user,),
                parent_transaction_kwargs={"currency": currency},
            )

        rows = SimpleDebtService.get_rows(room_id=room.id, viewer_id=user.id)

        assert len(rows) == 1
        assert rows[0].value == Decimal("26")

    def test_amounts_of_the_same_pair_stay_separate_across_currencies(self, room, user, guest_user):
        """The project has no exchange rates, so amounts of two currencies must never be added up."""
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))

        rows = SimpleDebtService.get_rows(room_id=room.id, viewer_id=user.id)

        assert len(rows) == 2
        assert {row.value for row in rows} == {Decimal("13")}
        assert len({row.currency.id for row in rows}) == 2

    def test_opposing_debts_of_a_pair_stay_separate_rows(self, room, user, guest_user):
        """The unoptimised view must not net anything - that is exactly what it contrasts with."""
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
        create_parent_transaction_with_optimisation(room=room, paid_by=guest_user, paid_for_tuple=(user,))

        rows = SimpleDebtService.get_rows(room_id=room.id, viewer_id=user.id)

        assert len(rows) == 2
        assert {(row.debitor.id, row.creditor.id) for row in rows} == {
            (guest_user.id, user.id),
            (user.id, guest_user.id),
        }

    def test_rows_ignore_settlements_of_the_optimised_debts(self, room, user, guest_user):
        create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
        debt = room.debts.get()
        debt.settled = True
        debt.save()

        rows = SimpleDebtService.get_rows(room_id=room.id, viewer_id=user.id)

        assert len(rows) == 1
        assert rows[0].settled is False
        assert rows[0].value == Decimal("13")

    def test_rows_are_ordered_by_debitor_name(self, room, user, guest_user):
        early_debitor = UserFactory(name="Aaron")
        late_debitor = UserFactory(name="Zoe")
        room.users.add(early_debitor, late_debitor)
        create_parent_transaction_with_optimisation(
            room=room, paid_by=user, paid_for_tuple=(late_debitor, early_debitor, guest_user)
        )

        rows = SimpleDebtService.get_rows(room_id=room.id, viewer_id=user.id)

        debitor_names = [row.debitor.name for row in rows]
        assert debitor_names == sorted(debitor_names)
