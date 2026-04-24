from decimal import Decimal
from types import SimpleNamespace

import pytest

from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.debt.models import Debt
from apps.debt.views.money_spent_on_room_view.money_spent_on_room_view import MoneySpentOnRoomView
from apps.room.tests.factories import RoomFactory
from apps.transaction.tests.factories import ChildTransactionFactory, ParentTransactionFactory


@pytest.mark.django_db
class TestMoneySpentOnRoomViewContext:
    def _view_for_room(self, room):
        view = MoneySpentOnRoomView()
        view.request = SimpleNamespace(room=room, GET={})
        return view

    def test_money_spent_per_person_qs_scopes_to_room(self, room, user, guest_user):
        other_room = RoomFactory(created_by=user)
        other_room.users.add(user)
        alien_currency = CurrencyFactory(sign="¤")
        other_parent = ParentTransactionFactory(room=other_room, paid_by=user, currency=alien_currency)
        ChildTransactionFactory.create(parent_transaction=other_parent, paid_for=guest_user, value=Decimal("5"))

        base_parent = ParentTransactionFactory(room=room, paid_by=user, currency=room.preferred_currency)
        ChildTransactionFactory.create(parent_transaction=base_parent, paid_for=guest_user, value=Decimal("7"))

        view = self._view_for_room(room)
        currency_signs = {entry["currency_sign"] for entry in view.money_spent_per_person_qs}

        assert alien_currency.sign not in currency_signs
        assert room.preferred_currency.sign in currency_signs

    def test_money_views_aggregate_totals_and_exclude_self_pay(self, room, guest_user):
        payer_primary = UserFactory(name="Primary Payer")
        payer_secondary = UserFactory(name="Secondary Payer")
        payee_third = UserFactory(name="Third Payee")
        room.users.add(payer_primary, payer_secondary, payee_third)

        currency_a = room.preferred_currency
        currency_b = CurrencyFactory(sign="¤")

        primary_txn = ParentTransactionFactory(room=room, paid_by=payer_primary, currency=currency_a)
        ChildTransactionFactory.create(parent_transaction=primary_txn, paid_for=guest_user, value=Decimal("10"))
        ChildTransactionFactory.create(parent_transaction=primary_txn, paid_for=payee_third, value=Decimal("5"))
        ChildTransactionFactory.create(parent_transaction=primary_txn, paid_for=payer_primary, value=Decimal("20"))

        secondary_txn = ParentTransactionFactory(room=room, paid_by=payer_secondary, currency=currency_b)
        ChildTransactionFactory.create(parent_transaction=secondary_txn, paid_for=guest_user, value=Decimal("7"))
        ChildTransactionFactory.create(parent_transaction=secondary_txn, paid_for=payer_primary, value=Decimal("3"))

        view = self._view_for_room(room)

        spent = list(view.money_spent_per_person_qs)
        spent_map = {
            (entry["paid_by_name"], entry["currency_sign"]): entry["total_spent_per_person"] for entry in spent
        }
        assert spent_map[(payer_primary.name, currency_a.sign)] == Decimal("35")
        assert spent_map[(payer_secondary.name, currency_b.sign)] == Decimal("10")

        total_spent = {entry["currency_sign"]: entry["total_spent"] for entry in view.total_money_spent}
        assert total_spent[currency_a.sign] == Decimal("35")
        assert total_spent[currency_b.sign] == Decimal("10")

        covered = list(view.money_covered_for_person_qs)
        covered_map = {
            (entry["paid_for__name"], entry["currency_sign"]): entry["total_covered_for_person"] for entry in covered
        }
        assert covered_map[(guest_user.name, currency_a.sign)] == Decimal("10")
        assert covered_map[(guest_user.name, currency_b.sign)] == Decimal("7")
        assert covered_map[(payee_third.name, currency_a.sign)] == Decimal("5")
        assert covered_map[(payer_primary.name, currency_b.sign)] == Decimal("3")
        assert (payer_primary.name, currency_a.sign) not in covered_map

    def test_open_debts_per_person_qs_only_returns_unsettled(self, room, user, guest_user):
        currency = room.preferred_currency
        open_debt = Debt.objects.create(
            debitor=guest_user,
            creditor=user,
            room=room,
            currency=currency,
            value=Decimal("12.50"),
            settled=False,
        )
        Debt.objects.create(
            debitor=guest_user,
            creditor=user,
            room=room,
            currency=currency,
            value=Decimal("5.00"),
            settled=True,
        )

        view = self._view_for_room(room)
        open_debts = list(view.open_debts_per_person_qs)

        assert len(open_debts) == 1
        assert open_debts[0]["debitor_name"] == guest_user.name
        assert open_debts[0]["total_open_debt"] == open_debt.value

    def test_max_open_debt_per_currency_reflects_max_unsettled(self, room, user, guest_user):
        currency = room.preferred_currency
        extra_user = UserFactory(name="Extra")
        room.users.add(extra_user)

        Debt.objects.create(debitor=guest_user, creditor=user, room=room, currency=currency, value=Decimal("30"), settled=False)
        Debt.objects.create(debitor=extra_user, creditor=user, room=room, currency=currency, value=Decimal("10"), settled=False)

        view = self._view_for_room(room)
        max_map = view.max_open_debt_per_currency

        assert max_map[currency.sign] == Decimal("30")
