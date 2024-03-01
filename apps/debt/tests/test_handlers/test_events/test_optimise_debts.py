from decimal import Decimal
from http import HTTPStatus

from django.urls import reverse
from freezegun import freeze_time
from model_bakery import baker

from apps.core.tests.setup import BaseTestSetUp
from apps.debt.models import Debt
from apps.transaction.tests.baker_recipes import create_parent_transaction_with_optimisation


class CalculateOptimisedDebtsTestCase(BaseTestSetUp):
    def test_simple_reduction_single_currency_no_settle(self):
        currency = baker.make_recipe("apps.currency.tests.currency")

        create_parent_transaction_with_optimisation(
            room=self.room,
            paid_by=self.user,
            paid_for_tuple=(self.user, self.guest_user),
            parent_transaction_kwargs={"currency": currency},
            child_transaction_kwargs={"value": Decimal(10)},
        )

        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=self.guest_user.id, room_id=self.room.id, currency_id=currency.id
            ),
            10,
        )
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=self.user.id, room_id=self.room.id, currency_id=currency.id
            ),
            10,
        )

        create_parent_transaction_with_optimisation(
            room=self.room,
            paid_by=self.guest_user,
            paid_for_tuple=(self.user,),
            parent_transaction_kwargs={"currency": currency},
            child_transaction_kwargs={"value": Decimal(5)},
        )

        self.assertEqual(self.guest_user.debts.count(), 1)

        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=self.guest_user.id, room_id=self.room.id, currency_id=currency.id
            ),
            5,
        )
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=self.user.id, room_id=self.room.id, currency_id=currency.id
            ),
            5,
        )

        self.assertEqual(self.user.debts.count(), 0)

    @freeze_time("2020-04-04 4:20:00")
    def test_simple_reduction_single_currency_with_settle(self):
        currency = baker.make_recipe("apps.currency.tests.currency")

        create_parent_transaction_with_optimisation(
            room=self.room,
            paid_by=self.user,
            paid_for_tuple=(self.user, self.guest_user),
            parent_transaction_kwargs={"currency": currency},
            child_transaction_kwargs={"value": Decimal(10)},
        )
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=self.guest_user.id, room_id=self.room.id, currency_id=currency.id
            ),
            10,
        )
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=self.user.id, room_id=self.room.id, currency_id=currency.id
            ),
            10,
        )

        create_parent_transaction_with_optimisation(
            room=self.room,
            paid_by=self.guest_user,
            paid_for_tuple=(self.user,),
            parent_transaction_kwargs={"currency": currency},
            child_transaction_kwargs={"value": Decimal(5)},
        )
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=self.guest_user.id, room_id=self.room.id, currency_id=currency.id
            ),
            5,
        )
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=self.user.id, room_id=self.room.id, currency_id=currency.id
            ),
            5,
        )

        debt = self.room.debts.first()
        response = self.client.post(
            reverse("debt:settle", kwargs={"room_slug": self.room.slug, "pk": debt.id}),
            data={"settled": True},
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertEqual(self.room.debts.filter(settled=False).count(), 0)

        create_parent_transaction_with_optimisation(
            room=self.room,
            paid_by=self.guest_user,
            paid_for_tuple=(self.user, self.guest_user),
            parent_transaction_kwargs={"currency": currency},
            child_transaction_kwargs={"value": Decimal(20)},
        )
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=self.user.id, room_id=self.room.id, currency_id=currency.id
            ),
            20,
        )
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=self.guest_user.id, room_id=self.room.id, currency_id=currency.id
            ),
            20,
        )

        create_parent_transaction_with_optimisation(
            room=self.room,
            paid_by=self.user,
            paid_for_tuple=(self.user, self.guest_user),
            parent_transaction_kwargs={"currency": currency},
            child_transaction_kwargs={"value": Decimal(15)},
        )
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=self.user.id, room_id=self.room.id, currency_id=currency.id
            ),
            15,
        )
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=self.guest_user.id, room_id=self.room.id, currency_id=currency.id
            ),
            15,
        )

        self.assertEqual(self.room.debts.filter(settled=False).count(), 1)

    def test_complicated_reduction_two_currencies_no_settle(self):
        currency_list = baker.make_recipe("apps.currency.tests.currency", _quantity=2)
        currency_1 = currency_list[0]
        currency_2 = currency_list[1]

        user_list = baker.make_recipe("apps.account.tests.user", _quantity=2)
        guest_user_list = baker.make_recipe("apps.account.tests.guest_user", _quantity=2)

        default_kwargs = {"room": self.room}
        currency_1_kwargs = {**default_kwargs, "parent_transaction_kwargs": {"currency": currency_1}}
        currency_2_kwargs = {**default_kwargs, "parent_transaction_kwargs": {"currency": currency_2}}

        self.room.users.add(*user_list + guest_user_list)

        user_1 = self.user
        user_2 = user_list[0]
        user_3 = user_list[1]
        guest_user_1 = self.guest_user
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
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=user_2.id, room_id=self.room.id, currency_id=currency_1.id
            ),
            20,
        )
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=guest_user_1.id, room_id=self.room.id, currency_id=currency_1.id
            ),
            10,
        )
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=user_1.id, room_id=self.room.id, currency_id=currency_1.id
            ),
            10,
        )
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=user_3.id, room_id=self.room.id, currency_id=currency_1.id
            ),
            20,
        )

        # Assert currency_2 statements
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=guest_user_2.id, room_id=self.room.id, currency_id=currency_2.id
            ),
            10,
        )
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=user_3.id, room_id=self.room.id, currency_id=currency_2.id
            ),
            10,
        )
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_to_others_for_a_room(
                debitor_id=user_3.id, room_id=self.room.id, currency_id=currency_2.id
            ),
            10,
        )
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=user_2.id, room_id=self.room.id, currency_id=currency_2.id
            ),
            20,
        )
        self.assertEqual(
            Debt.objects.get_total_money_of_currency_still_owed_by_others_for_a_room(
                creditor_id=guest_user_3.id, room_id=self.room.id, currency_id=currency_2.id
            ),
            10,
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

        self.assertEqual(self.room.debts.count(), 0)
