from decimal import Decimal

import pytest
from django.urls import reverse

from apps.currency.tests.factories import CurrencyFactory
from apps.debt.models import Debt
from apps.room.models import Room
from apps.room.services.room_overview_service import RoomOverviewService
from apps.room.tests.factories import RoomFactory

pytestmark = pytest.mark.django_db


def create_debt(*, room, debitor, creditor, currency, value):
    return Debt.objects.create(
        room=room,
        debitor=debitor,
        creditor=creditor,
        currency=currency,
        value=Decimal(value),
    )


def entry_for(entries, room):
    return next(entry for entry in entries if entry.slug == room.slug)


class TestRoomOverviewService:
    def test_open_room_points_at_the_transaction_list(self, room, user):
        entries = RoomOverviewService(user=user).get_entries()

        assert entry_for(entries, room).target_url == reverse("transaction:list", kwargs={"room_slug": room.slug})

    def test_closed_room_points_at_the_room_detail(self, closed_room, user):
        entries = RoomOverviewService(user=user).get_entries()

        entry = entry_for(entries, closed_room)
        assert entry.is_closed is True
        assert entry.target_url == reverse("room:detail", kwargs={"room_slug": closed_room.slug})

    def test_status_label_is_resolved(self, room, closed_room, user):
        entries = RoomOverviewService(user=user).get_entries()

        assert entry_for(entries, room).status_label == Room.StatusChoices.OPEN.label
        assert entry_for(entries, closed_room).status_label == Room.StatusChoices.CLOSED.label

    def test_balance_is_attached_to_the_right_room_with_the_right_sign(self, room, user, guest_user):
        currency = CurrencyFactory(sign="€")
        other_room = RoomFactory(created_by=user)
        other_room.users.add(user, guest_user)
        create_debt(room=room, debitor=user, creditor=guest_user, currency=currency, value="10.00")
        create_debt(room=other_room, debitor=guest_user, creditor=user, currency=currency, value="7.00")

        entries = RoomOverviewService(user=user).get_entries()

        owing_balance = entry_for(entries, room).balances[0]
        assert owing_balance.user_owes is True
        assert owing_balance.absolute_amount == Decimal("10.00")

        receiving_balance = entry_for(entries, other_room).balances[0]
        assert receiving_balance.user_owes is False
        assert receiving_balance.absolute_amount == Decimal("7.00")

    def test_a_net_zero_balance_stays_visible_as_balanced(self, room, user, guest_user):
        currency = CurrencyFactory()
        create_debt(room=room, debitor=user, creditor=guest_user, currency=currency, value="10.00")
        create_debt(room=room, debitor=guest_user, creditor=user, currency=currency, value="10.00")

        balances = entry_for(RoomOverviewService(user=user).get_entries(), room).balances

        assert len(balances) == 1
        assert balances[0].is_balanced is True

    def test_a_room_without_open_debts_has_no_balances(self, room, user):
        assert entry_for(RoomOverviewService(user=user).get_entries(), room).balances == ()

    def test_currencies_sharing_a_sign_stay_separate(self, room, user, guest_user):
        # Currency has no unique constraint on sign or code, so USD and CAD can both use "$".
        usd = CurrencyFactory(code="USD", sign="$")
        cad = CurrencyFactory(code="CAD", sign="$")
        create_debt(room=room, debitor=user, creditor=guest_user, currency=usd, value="10.00")
        create_debt(room=room, debitor=user, creditor=guest_user, currency=cad, value="5.00")

        balances = entry_for(RoomOverviewService(user=user).get_entries(), room).balances

        assert len(balances) == 2
        assert sorted(balance.absolute_amount for balance in balances) == [Decimal("5.00"), Decimal("10.00")]

    def test_superuser_sees_foreign_rooms_without_balances(self, room, superuser):
        entries = RoomOverviewService(user=superuser).get_entries()

        entry = entry_for(entries, room)
        assert entry.user_is_in_room is False
        assert entry.balances == ()

    def test_entries_keep_the_ordering_of_room_qs_for_list(self, room, closed_room, user):
        entries = RoomOverviewService(user=user).get_entries()

        assert [entry.slug for entry in entries] == [values["slug"] for values in user.room_qs_for_list]

    @pytest.mark.parametrize("extra_room_count", [1, 5])
    def test_building_the_entries_takes_two_queries(
        self, user, guest_user, django_assert_num_queries, extra_room_count
    ):
        currency = CurrencyFactory()
        for _ in range(extra_room_count):
            extra_room = RoomFactory(created_by=user)
            extra_room.users.add(user, guest_user)
            create_debt(room=extra_room, debitor=user, creditor=guest_user, currency=currency, value="3.00")

        service = RoomOverviewService(user=user)
        with django_assert_num_queries(2):
            entries = service.get_entries()

        assert len(entries) == extra_room_count

    def test_the_two_directions_stay_apart(self, room, user, guest_user):
        currency = CurrencyFactory(sign="€")
        other_room = RoomFactory(created_by=user)
        other_room.users.add(user, guest_user)
        create_debt(room=room, debitor=user, creditor=guest_user, currency=currency, value="10.00")
        create_debt(room=other_room, debitor=guest_user, creditor=user, currency=currency, value="7.00")

        totals = RoomOverviewService.currency_totals_for(RoomOverviewService(user=user).get_entries())

        assert len(totals) == 1
        assert totals[0].owed_by_user == Decimal("10.00")
        assert totals[0].owed_to_user == Decimal("7.00")

    def test_amounts_of_one_currency_are_summed_across_rooms(self, room, user, guest_user):
        currency = CurrencyFactory(sign="€")
        other_room = RoomFactory(created_by=user)
        other_room.users.add(user, guest_user)
        create_debt(room=room, debitor=user, creditor=guest_user, currency=currency, value="10.00")
        create_debt(room=other_room, debitor=user, creditor=guest_user, currency=currency, value="2.50")

        totals = RoomOverviewService.currency_totals_for(RoomOverviewService(user=user).get_entries())

        assert [total.owed_by_user for total in totals] == [Decimal("12.50")]

    def test_currencies_sharing_a_sign_are_not_merged(self, room, user, guest_user):
        # Currency has no unique constraint on sign, so grouping by sign would add USD to CAD.
        usd = CurrencyFactory(code="USD", sign="$")
        cad = CurrencyFactory(code="CAD", sign="$")
        create_debt(room=room, debitor=user, creditor=guest_user, currency=usd, value="10.00")
        create_debt(room=room, debitor=user, creditor=guest_user, currency=cad, value="5.00")

        totals = RoomOverviewService.currency_totals_for(RoomOverviewService(user=user).get_entries())

        assert len(totals) == 2
        assert {total.currency_id for total in totals} == {usd.id, cad.id}
        assert [total.owed_by_user for total in totals] == [Decimal("10.00"), Decimal("5.00")]

    def test_a_room_that_nets_to_zero_contributes_nothing(self, room, user, guest_user):
        currency = CurrencyFactory()
        create_debt(room=room, debitor=user, creditor=guest_user, currency=currency, value="10.00")
        create_debt(room=room, debitor=guest_user, creditor=user, currency=currency, value="10.00")

        assert RoomOverviewService.currency_totals_for(RoomOverviewService(user=user).get_entries()) == []

    def test_a_user_without_debts_has_no_totals(self, room, user):
        assert RoomOverviewService.currency_totals_for(RoomOverviewService(user=user).get_entries()) == []

    def test_totals_need_no_further_query(self, room, user, guest_user, django_assert_num_queries):
        create_debt(room=room, debitor=user, creditor=guest_user, currency=CurrencyFactory(), value="4.00")
        entries = RoomOverviewService(user=user).get_entries()

        with django_assert_num_queries(0):
            RoomOverviewService.currency_totals_for(entries)
