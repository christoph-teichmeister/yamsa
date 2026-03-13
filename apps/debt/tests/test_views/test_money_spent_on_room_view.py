from decimal import Decimal
from types import SimpleNamespace

import pytest

from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
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

        owed = list(view.money_owed_per_person_qs)
        owed_map = {(entry["paid_for__name"], entry["currency_sign"]): entry["total_owed_per_person"] for entry in owed}
        assert owed_map[(guest_user.name, currency_a.sign)] == Decimal("10")
        assert owed_map[(guest_user.name, currency_b.sign)] == Decimal("7")
        assert owed_map[(payee_third.name, currency_a.sign)] == Decimal("5")
        assert owed_map[(payer_primary.name, currency_b.sign)] == Decimal("3")
        assert (payer_primary.name, currency_a.sign) not in owed_map
