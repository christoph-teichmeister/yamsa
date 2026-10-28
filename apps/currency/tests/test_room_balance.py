from decimal import Decimal

import pytest

from apps.currency.tests.factories import CurrencyFactory
from apps.room.dataclasses import RoomBalance


def _balance(owed_by_user: str, owed_to_user: str, currency_id: int = 1, sign: str = "€") -> RoomBalance:
    return RoomBalance(
        currency_id=currency_id,
        currency_sign=sign,
        owed_by_user=Decimal(owed_by_user),
        owed_to_user=Decimal(owed_to_user),
    )


class TestRoomBalance:
    def test_net_amount_is_what_the_user_gets_minus_what_the_user_owes(self) -> None:
        assert _balance("10.00", "25.50").net_amount == Decimal("15.50")
        assert _balance("25.50", "10.00").net_amount == Decimal("-15.50")

    def test_a_negative_net_means_the_user_owes(self) -> None:
        balance = _balance("30", "10")

        assert balance.user_owes
        assert not balance.user_gets_back
        assert not balance.is_balanced
        assert balance.absolute_amount == Decimal(20)

    def test_a_positive_net_means_the_user_gets_back(self) -> None:
        balance = _balance("10", "30")

        assert balance.user_gets_back
        assert not balance.user_owes
        assert not balance.is_balanced

    def test_open_debts_that_cancel_out_are_balanced_not_absent(self) -> None:
        balance = _balance("12.34", "12.34")

        assert balance.is_balanced
        assert not balance.user_owes
        assert not balance.user_gets_back
        assert balance.absolute_amount == Decimal(0)

    def test_the_balance_is_immutable(self) -> None:
        with pytest.raises(AttributeError):
            _balance("1", "2").owed_by_user = Decimal(5)  # type: ignore[misc]

    @pytest.mark.django_db
    def test_currencies_sharing_a_sign_stay_separate_balances(self) -> None:
        usd = CurrencyFactory(code="USD", sign="$")
        cad = CurrencyFactory(code="CAD", sign="$")
        owed_in_usd = _balance("50", "0", currency_id=usd.pk, sign=usd.sign)
        gets_in_cad = _balance("0", "50", currency_id=cad.pk, sign=cad.sign)

        assert owed_in_usd.currency_sign == gets_in_cad.currency_sign
        assert owed_in_usd.currency_id != gets_in_cad.currency_id
        assert owed_in_usd != gets_in_cad
        assert owed_in_usd.user_owes
        assert gets_in_cad.user_gets_back

    def test_amounts_of_different_currencies_are_never_netted(self) -> None:
        balances = [_balance("50", "0", currency_id=1, sign="$"), _balance("0", "50", currency_id=2, sign="$")]

        assert [b.net_amount for b in balances] == [Decimal(-50), Decimal(50)]
        assert not any(b.is_balanced for b in balances)
