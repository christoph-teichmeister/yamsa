from decimal import Decimal

import pytest

from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.debt.models import Debt
from apps.room.tests.factories import RoomFactory

pytestmark = pytest.mark.django_db


def create_debt(*, room, debitor, creditor, currency, value, settled=False):
    return Debt.objects.create(
        room=room,
        debitor=debitor,
        creditor=creditor,
        currency=currency,
        value=Decimal(value),
        settled=settled,
    )


def balance_rows_for(user):
    return list(
        Debt.objects.filter_open()
        .filter_involving_user(user_id=user.id)
        .aggregate_balance_per_room_and_currency(user_id=user.id)
    )


class TestDebtQuerySet:
    def test_currencies_of_one_room_stay_separate(self, room, user, guest_user):
        currency_1 = CurrencyFactory(sign="€")
        currency_2 = CurrencyFactory(sign="$")
        create_debt(room=room, debitor=user, creditor=guest_user, currency=currency_1, value="10.00")
        create_debt(room=room, debitor=user, creditor=guest_user, currency=currency_2, value="4.00")

        rows = balance_rows_for(user)

        assert len(rows) == 2
        by_sign = {row["currency_sign"]: row for row in rows}
        assert by_sign["€"]["owed_by_user"] == Decimal("10.00")
        assert by_sign["$"]["owed_by_user"] == Decimal("4.00")

    def test_currencies_sharing_a_sign_stay_separate(self, room, user, guest_user):
        # Currency has no unique constraint on sign or code, so USD and CAD can both use "$".
        usd = CurrencyFactory(code="USD", sign="$")
        cad = CurrencyFactory(code="CAD", sign="$")
        create_debt(room=room, debitor=user, creditor=guest_user, currency=usd, value="10.00")
        create_debt(room=room, debitor=user, creditor=guest_user, currency=cad, value="5.00")

        rows = balance_rows_for(user)

        assert len(rows) == 2
        assert sorted(row["owed_by_user"] for row in rows) == [Decimal("5.00"), Decimal("10.00")]

    def test_both_sides_of_the_same_room_and_currency_are_aggregated_into_one_row(self, room, user, guest_user):
        currency = CurrencyFactory()
        create_debt(room=room, debitor=user, creditor=guest_user, currency=currency, value="10.00")
        create_debt(room=room, debitor=guest_user, creditor=user, currency=currency, value="4.00")

        rows = balance_rows_for(user)

        assert len(rows) == 1
        assert rows[0]["owed_by_user"] == Decimal("10.00")
        assert rows[0]["owed_to_user"] == Decimal("4.00")

    def test_settled_debts_are_excluded(self, room, user, guest_user):
        currency = CurrencyFactory()
        create_debt(room=room, debitor=user, creditor=guest_user, currency=currency, value="10.00", settled=True)

        assert balance_rows_for(user) == []

    def test_debts_between_other_users_are_excluded(self, room, user, guest_user):
        other_user = UserFactory()
        room.users.add(other_user)
        currency = CurrencyFactory()
        create_debt(room=room, debitor=guest_user, creditor=other_user, currency=currency, value="10.00")

        assert balance_rows_for(user) == []

    def test_rooms_without_debts_produce_no_row(self, room, user, guest_user):
        currency = CurrencyFactory()
        other_room = RoomFactory(created_by=user)
        other_room.users.add(user)
        create_debt(room=room, debitor=user, creditor=guest_user, currency=currency, value="10.00")

        rows = balance_rows_for(user)

        assert [row["room_id"] for row in rows] == [room.id]

    def test_aggregation_takes_a_single_query_regardless_of_room_count(
        self, user, guest_user, django_assert_num_queries
    ):
        currency = CurrencyFactory()
        for _ in range(5):
            extra_room = RoomFactory(created_by=user)
            extra_room.users.add(user, guest_user)
            create_debt(room=extra_room, debitor=user, creditor=guest_user, currency=currency, value="3.00")

        with django_assert_num_queries(1):
            rows = balance_rows_for(user)

        assert len(rows) == 5
