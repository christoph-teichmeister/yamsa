from decimal import Decimal
from http import HTTPStatus

import pytest
from django.urls import reverse
from freezegun import freeze_time

from apps.account.tests.factories import GuestUserFactory, UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.debt.models import Debt
from apps.transaction.tests.baker_recipes import create_parent_transaction_with_optimisation


@pytest.mark.django_db
class TestCalculateOptimisedDebts:
    def test_simple_reduction_single_currency_no_settle(self, room, user, guest_user):
        currency = CurrencyFactory()

        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(user, guest_user),
            parent_transaction_kwargs={"currency": currency},
            child_transaction_kwargs={"value": Decimal(10)},
        )

        assert (
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=guest_user.id, room_id=room.id, currency_id=currency.id
            )
            == 10
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=user.id, room_id=room.id, currency_id=currency.id
            )
            == 10
        )

        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=guest_user,
            paid_for_tuple=(user,),
            parent_transaction_kwargs={"currency": currency},
            child_transaction_kwargs={"value": Decimal(5)},
        )

        assert guest_user.debts.count() == 1

        assert (
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=guest_user.id, room_id=room.id, currency_id=currency.id
            )
            == 5
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=user.id, room_id=room.id, currency_id=currency.id
            )
            == 5
        )

        assert user.debts.count() == 0

    @freeze_time("2020-04-04 4:20:00")
    def test_simple_reduction_single_currency_with_settle(self, room, user, guest_user, authenticated_client):
        currency = CurrencyFactory()

        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(user, guest_user),
            parent_transaction_kwargs={"currency": currency},
            child_transaction_kwargs={"value": Decimal(10)},
        )
        """
        guest_user owes 10 to user
        user owes 10 to "themselves"
        """
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=guest_user.id, room_id=room.id, currency_id=currency.id
            )
            == 10
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=user.id, room_id=room.id, currency_id=currency.id
            )
            == 10
        )

        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=guest_user,
            paid_for_tuple=(user,),
            parent_transaction_kwargs={"currency": currency},
            child_transaction_kwargs={"value": Decimal(5)},
        )
        """
        guest_user now owes 5 to user
        user technically still owes 10 to "themselves"
        """
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=guest_user.id, room_id=room.id, currency_id=currency.id
            )
            == 5
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=user.id, room_id=room.id, currency_id=currency.id
            )
            == 5
        )

        debt = room.debts.get(creditor_id=user.id, debitor_id=guest_user.id, currency_id=currency.id, value=Decimal(5))
        response = authenticated_client.post(
            reverse("debt:settle", kwargs={"room_slug": room.slug, "pk": debt.id}),
            data={"settled": True},
            follow=True,
        )
        assert response.status_code == HTTPStatus.OK

        # All debts are settled, noone owes anything to anyone
        assert room.debts.filter(settled=False).count() == 0

        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=guest_user,
            paid_for_tuple=(user, guest_user),
            parent_transaction_kwargs={"currency": currency},
            child_transaction_kwargs={"value": Decimal(20)},
        )
        """
        user now owes 20 to guest_user
        guest_user technically owes 20 to themselves
        """
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=user.id, room_id=room.id, currency_id=currency.id
            )
            == 20
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=guest_user.id, room_id=room.id, currency_id=currency.id
            )
            == 20
        )

        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(user, guest_user),
            parent_transaction_kwargs={"currency": currency},
            child_transaction_kwargs={"value": Decimal(15)},
        )
        """
        user now owes 5 to guest_user
        """
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=user.id, room_id=room.id, currency_id=currency.id
            )
            == 5
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=guest_user.id, room_id=room.id, currency_id=currency.id
            )
            == 5
        )

        assert room.debts.filter(settled=False).count() == 1

    def test_complicated_reduction_two_currencies_no_settle(self, room, user, guest_user):
        currency_list = [CurrencyFactory(), CurrencyFactory()]
        currency_1 = currency_list[0]
        currency_2 = currency_list[1]

        user_list = [UserFactory(), UserFactory()]
        guest_user_list = [GuestUserFactory(), GuestUserFactory()]

        default_kwargs = {"room": room}
        currency_1_kwargs = {**default_kwargs, "parent_transaction_kwargs": {"currency": currency_1}}
        currency_2_kwargs = {**default_kwargs, "parent_transaction_kwargs": {"currency": currency_2}}

        room.users.add(*user_list + guest_user_list)

        user_1 = user
        user_2 = user_list[0]
        user_3 = user_list[1]
        guest_user_1 = guest_user
        guest_user_2 = guest_user_list[0]
        guest_user_3 = guest_user_list[1]

        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=user_1,
            paid_for_tuple=(user_1, user_2, guest_user_1),
            child_transaction_kwargs={"value": Decimal(10)},
        )
        """
        currency_1:
            user_1:
                user_2:         10
                guest_user_1:   10
        """

        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=user_3,
            paid_for_tuple=(user_2, user_3, guest_user_1),
            child_transaction_kwargs={"value": Decimal(10)},
        )
        """
        currency_1:
            user_1:
                user_2:         10
                guest_user_1:   10
            user_3:
                user_2:         10
                guest_user_1:   10
        """

        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=guest_user_1,
            paid_for_tuple=(user_1, guest_user_1),
            child_transaction_kwargs={"value": Decimal(10)},
        )
        """
        currency_1:
            user_1:
                user_2:         10
                guest_user_1:   10
            user_3:
                user_2:         10
                guest_user_1:   10
            guest_user_1:
                user_1:         10

        ==>

        currency_1:
            user_1:
                user_2:         10
            user_3:
                user_2:         10
                guest_user_1:   10>
        """

        create_parent_transaction_with_optimisation(
            **currency_2_kwargs,
            paid_by=user_2,
            paid_for_tuple=(user_2, guest_user_2, user_3),
            child_transaction_kwargs={"value": Decimal(10)},
        )
        """
        currency_1:
            user_1:
                user_2:         10
            user_3:
                user_2:         10
                guest_user_1:   10
        currency_2:
            user_2:
                guest_user_2:   10
                user_3:         10
        """

        create_parent_transaction_with_optimisation(
            **currency_2_kwargs,
            paid_by=guest_user_3,
            paid_for_tuple=(user_1,),
            child_transaction_kwargs={"value": Decimal(10)},
        )
        """
        currency_1:
            user_1:
                user_2:         10
            user_3:
                user_2:         10
                guest_user_1:   10
        currency_2:
            user_2:
                guest_user_2:   10
                user_3:         10
            guest_user_3:
                user_1:         10
        """

        """
        At this point, we can say the following:

        currency_1:
            user_2 owes 20
            guest_user_1 owes 10

            user_1 receives 10
            user_3 receives 20
        currency_2:
            guest_user_2 owes 10
            user_3 owes 10
            user_1 owes 10

            user_2 receives 20
            guest_user_3 receives 10
        """

        # --- Assert the above statements ---

        # Assert currency_1 statements
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=user_2.id, room_id=room.id, currency_id=currency_1.id
            )
            == 20
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=guest_user_1.id, room_id=room.id, currency_id=currency_1.id
            )
            == 10
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=user_1.id, room_id=room.id, currency_id=currency_1.id
            )
            == 10
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=user_3.id, room_id=room.id, currency_id=currency_1.id
            )
            == 20
        )

        # Assert currency_2 statements
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=guest_user_2.id, room_id=room.id, currency_id=currency_2.id
            )
            == 10
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=user_3.id, room_id=room.id, currency_id=currency_2.id
            )
            == 10
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=user_3.id, room_id=room.id, currency_id=currency_2.id
            )
            == 10
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=user_2.id, room_id=room.id, currency_id=currency_2.id
            )
            == 20
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=guest_user_3.id, room_id=room.id, currency_id=currency_2.id
            )
            == 10
        )

        # --------------- now we revert to 0 debts by "smart" payments

        """
        currency_1:
            user_1:
                user_2:         10
            user_3:
                user_2:         10
                guest_user_1:   10
        currency_2:
            user_2:
                guest_user_2:   10
                user_3:         10
            guest_user_3:
                user_1:         10
        """
        create_parent_transaction_with_optimisation(
            **currency_2_kwargs,
            paid_by=user_1,
            paid_for_tuple=(user_2,),
            child_transaction_kwargs={"value": Decimal(10)},
        )
        """
        currency_1:
            user_1:
                user_2:         10
            user_3:
                user_2:         10
                guest_user_1:   10
        currency_2:
            user_2:
                guest_user_2:   10
                user_3:         10
            guest_user_3:
                user_1:         10
            user_1:
                user_2          10
        """

        create_parent_transaction_with_optimisation(
            **currency_2_kwargs,
            paid_by=user_3,
            paid_for_tuple=(user_2,),
            child_transaction_kwargs={"value": Decimal(10)},
        )
        """
        currency_1:
            user_1:
                user_2:         10
            user_3:
                user_2:         10
                guest_user_1:   10
        currency_2:
            user_2:
                guest_user_2:   10
            guest_user_3:
                user_1:         10
            user_1:
                user_2          10
        """

        create_parent_transaction_with_optimisation(
            **currency_2_kwargs,
            paid_by=guest_user_2,
            paid_for_tuple=(guest_user_3,),
            child_transaction_kwargs={"value": Decimal(10)},
        )
        """
        currency_1:
            user_1:
                user_2:         10
            user_3:
                user_2:         10
                guest_user_1:   10
        currency_2:
            user_2:
                guest_user_2:   10
            guest_user_3:
                user_1:         10
            user_1:
                user_2          10
            guest_user_2:
                guest_user_3    10

        ^ the above currency_2 debts can be just swapped around, as it does not matter, who pays whom
        =>
        ...
        currency_2:
            user_2:
                guest_user_2:   10
            guest_user_2:
                user_2    10
            guest_user_3:
                user_1:         10
            user_1:
                guest_user_3    10

        => now, currency_2 eliminates itself, and we are left with currency_1:

        currency_1:
            user_1:
                user_2:         10
            user_3:
                user_2:         10
                guest_user_1:   10
        """

        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=user_2,
            paid_for_tuple=(user_1,),
            child_transaction_kwargs={"value": Decimal(20)},
        )
        """
        currency_1:
            user_1:
                user_2:         10
            user_3:
                user_2:         10
                guest_user_1:   10
            user_2:
                user_1:         20

        which can be rewritten to =>

        currency_1:
            user_3:
                user_1:         10
                guest_user_1:   10

        user_2 "moved" their debts to user_1
        """

        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=user_1,
            paid_for_tuple=(user_3,),
            child_transaction_kwargs={"value": Decimal(10)},
        )
        """
        currency_1:
            user_3:
                user_1:         10
                guest_user_1:   10
            user_1:
                user_3: 10

        =>

        currency_1:
            user_3:
                guest_user_1:   10
        """

        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=guest_user_1,
            paid_for_tuple=(user_3,),
            child_transaction_kwargs={"value": Decimal(10)},
        )
        """
        currency_1:
            user_3:
                guest_user_1:   10
            guest_user_1:
                user_3:         10

        => currency_1 eliminates itself
        """

        # Assert, that all debts have been cleared, and no debts remain

        assert room.debts.count() == 0

    @freeze_time("2020-04-04 4:20:00")
    def test_complicated_reduction_two_currencies_with_settle(self, room, user, guest_user, authenticated_client):
        currency_list = [CurrencyFactory(), CurrencyFactory()]
        currency_1 = currency_list[0]
        currency_2 = currency_list[1]

        user_1 = user
        user_2 = UserFactory()

        guest_user_1 = guest_user
        guest_user_2 = GuestUserFactory()

        default_kwargs = {"room": room}
        currency_1_kwargs = {**default_kwargs, "parent_transaction_kwargs": {"currency": currency_1}}
        currency_2_kwargs = {**default_kwargs, "parent_transaction_kwargs": {"currency": currency_2}}

        room.users.add(user_2, guest_user_2)

        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=user_1,
            paid_for_tuple=(user_1, user_2, guest_user_1),
            child_transaction_kwargs={"value": Decimal(5)},
        )
        """
        currency_1:
            user_1:
                user_2:         5
                guest_user_1:   5
        """

        assert (
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=user_2, room_id=room.id, currency_id=currency_1.id
            )
            == 5
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=guest_user_1, room_id=room.id, currency_id=currency_1.id
            )
            == 5
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=user_1, room_id=room.id, currency_id=currency_1.id
            )
            == 10
        )

        debt = room.debts.get(debitor=user_2, creditor=user_1)
        response = authenticated_client.post(
            reverse("debt:settle", kwargs={"room_slug": room.slug, "pk": debt.id}),
            data={"settled": True},
            follow=True,
        )
        assert response.status_code == HTTPStatus.OK
        """
        currency_1:
            user_1:
                guest_user_1:   5
        """

        assert (
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=guest_user_1, room_id=room.id, currency_id=currency_1.id
            )
            == 5
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=user_1, room_id=room.id, currency_id=currency_1.id
            )
            == 5
        )

        create_parent_transaction_with_optimisation(
            **currency_2_kwargs,
            paid_by=user_1,
            paid_for_tuple=(user_1, guest_user_1),
            child_transaction_kwargs={"value": Decimal(10)},
        )
        """
        currency_1:
            user_1:
                guest_user_1:   5
        currency_2:
            user_1:
                guest_user_1:   10
        """
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=guest_user_1, room_id=room.id, currency_id=currency_2.id
            )
            == 10
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=user_1, room_id=room.id, currency_id=currency_2.id
            )
            == 10
        )

        create_parent_transaction_with_optimisation(
            **currency_2_kwargs,
            paid_by=guest_user_2,
            paid_for_tuple=(user_1, guest_user_1),
            child_transaction_kwargs={"value": Decimal(5)},
        )
        """
        currency_1:
            user_1:
                guest_user_1:   5
        currency_2:
            user_1:
                guest_user_1:   10
            guest_user_3:
                user_1:         5
                guest_user_1:   5

            => user_1 would receive 10 currency_2 units from guest_user_1 and would have to pay them forward to
            guest_user_3. This operation can be reduced, if guest_user_1 reduces their currency_2 debt to user_1 by
            the amount user_1 owes guest_user_3, resulting in:

        currency_1:
            user_1:
                guest_user_1:   5
        currency_2:
            user_1:
                guest_user_1:   5
            guest_user_3:
                guest_user_1:   10
        """
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=guest_user_1, room_id=room.id, currency_id=currency_2.id
            )
            == 15
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=user_1, room_id=room.id, currency_id=currency_2.id
            )
            == 5
        )
        assert (
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=guest_user_2, room_id=room.id, currency_id=currency_2.id
            )
            == 10
        )

        debt = room.debts.get(debitor=guest_user_1, creditor=user_1, currency=currency_1)
        response = authenticated_client.post(
            reverse("debt:settle", kwargs={"room_slug": room.slug, "pk": debt.id}),
            data={"settled": True},
            follow=True,
        )
        assert response.status_code == HTTPStatus.OK
        """
        currency_2:
            user_1:
                guest_user_1:   5
            guest_user_3:
                guest_user_1:   10
        """

        create_parent_transaction_with_optimisation(
            **currency_2_kwargs,
            paid_by=guest_user_1,
            paid_for_tuple=(user_1, guest_user_2),
            child_transaction_kwargs={"value": Decimal(5)},
        )
        """
        currency_2:
            guest_user_3:
                guest_user_1:   5
        """

        debt = room.debts.get(debitor=guest_user_1, creditor=guest_user_2, currency=currency_2)
        response = authenticated_client.post(
            reverse("debt:settle", kwargs={"room_slug": room.slug, "pk": debt.id}),
            data={"settled": True},
            follow=True,
        )
        assert response.status_code == HTTPStatus.OK

        # Now, all debts should be settled
        assert room.debts.filter(settled=False).count() == 0

    @freeze_time("2020-04-04 4:20:00")
    def test_debt_optimisation_bug_real_life_example(self, room, user, guest_user):
        currency_1 = CurrencyFactory()

        chris = user
        carina = UserFactory()
        oliver = UserFactory()
        rici = guest_user

        default_kwargs = {"room": room}
        currency_1_kwargs = {**default_kwargs, "parent_transaction_kwargs": {"currency": currency_1}}

        room.users.add(carina, oliver)

        # Create all transactions of room

        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=oliver,
            paid_for_tuple=(oliver, chris, carina, rici),
            child_transaction_kwargs={"value": Decimal("18.75")},
        )
        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=oliver,
            paid_for_tuple=(chris,),
            child_transaction_kwargs={"value": Decimal("8.50")},
        )
        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=oliver,
            paid_for_tuple=(oliver, rici),
            child_transaction_kwargs={"value": Decimal(5)},
        )
        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=oliver,
            paid_for_tuple=(oliver, chris, carina, rici),
            child_transaction_kwargs={"value": Decimal(25)},
        )
        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=oliver,
            paid_for_tuple=(oliver, chris, carina, rici),
            child_transaction_kwargs={"value": Decimal("2.06")},
        )
        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=chris,
            paid_for_tuple=(oliver, rici, carina, chris),
            child_transaction_kwargs={"value": Decimal("13.12")},
        )
        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=oliver,
            paid_for_tuple=(oliver, rici, carina, chris),
            child_transaction_kwargs={"value": Decimal("2.75")},
        )
        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=oliver,
            paid_for_tuple=(oliver, rici, carina, chris),
            child_transaction_kwargs={"value": Decimal("7.50")},
        )
        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=chris,
            paid_for_tuple=(oliver, rici, carina, chris),
            child_transaction_kwargs={"value": Decimal("12.50")},
        )
        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=carina,
            paid_for_tuple=(oliver, rici, carina, chris),
            child_transaction_kwargs={"value": Decimal("12.50")},
        )
        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=oliver,
            paid_for_tuple=(oliver, rici, carina, chris),
            child_transaction_kwargs={"value": Decimal(6)},
        )
        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=oliver,
            paid_for_tuple=(oliver, carina),
            child_transaction_kwargs={"value": Decimal(4)},
        )
        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=oliver,
            paid_for_tuple=(oliver, rici, carina, chris),
            child_transaction_kwargs={"value": Decimal(2)},
        )
        create_parent_transaction_with_optimisation(
            **currency_1_kwargs,
            paid_by=chris,
            paid_for_tuple=(oliver, rici, carina, chris),
            child_transaction_kwargs={"value": Decimal("20.35")},
        )

        # Assert general debts
        assert Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
            debitor_id=carina.id, room_id=room.id, currency_id=currency_1.id
        ) == Decimal("76.53")
        assert Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
            debitor_id=rici.id, room_id=room.id, currency_id=currency_1.id
        ) == Decimal("127.53")
        assert Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
            debitor_id=chris.id, room_id=room.id, currency_id=currency_1.id
        ) == Decimal("0")
        assert Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
            debitor_id=oliver.id, room_id=room.id, currency_id=currency_1.id
        ) == Decimal("0")

        assert Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
            creditor_id=rici.id, room_id=room.id, currency_id=currency_1.id
        ) == Decimal("0")
        assert Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
            creditor_id=carina.id, room_id=room.id, currency_id=currency_1.id
        ) == Decimal("0")
        assert Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
            creditor_id=chris.id, room_id=room.id, currency_id=currency_1.id
        ) == Decimal("52.85")
        assert Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
            creditor_id=oliver.id, room_id=room.id, currency_id=currency_1.id
        ) == Decimal("151.21")

        # Assert Transaction-Proposals
        carina_debt_to_chris = Debt.objects.filter(
            creditor_id=chris.id, debitor_id=carina.id, room_id=room.id, currency_id=currency_1.id
        )
        assert carina_debt_to_chris.exists()
        assert carina_debt_to_chris.first().value == Decimal("52.85")

        carina_debt_to_oliver = Debt.objects.filter(
            creditor_id=oliver.id, debitor_id=carina.id, room_id=room.id, currency_id=currency_1.id
        )
        assert carina_debt_to_oliver.exists()
        assert carina_debt_to_oliver.first().value == Decimal("23.68")

        rici_debt_to_oliver = Debt.objects.filter(
            creditor_id=oliver.id, debitor_id=rici.id, room_id=room.id, currency_id=currency_1.id
        )
        assert rici_debt_to_oliver.exists()
        assert rici_debt_to_oliver.first().value == Decimal("127.53")
