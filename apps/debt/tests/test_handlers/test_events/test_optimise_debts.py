from decimal import Decimal

from model_bakery import baker

from apps.core.tests.setup import BaseTestSetUp
from apps.transaction.tests.baker_recipes import create_parent_transaction_with_optimisation


class CalculateOptimisedDebtsTestCase(BaseTestSetUp):
    def test_simple_reduction(self):
        currency = baker.make_recipe("apps.currency.tests.currency")

        create_parent_transaction_with_optimisation(
            room=self.room,
            paid_by=self.user,
            paid_for_tuple=(self.user, self.guest_user),
            parent_transaction_kwargs={"currency": currency},
            child_transaction_kwargs={"value": Decimal(10)},
        )

        guest_user_debt = self.guest_user.debts.first()
        self.assertEqual(guest_user_debt.value, Decimal(10))
        self.assertEqual(guest_user_debt.creditor, self.user)

        create_parent_transaction_with_optimisation(
            room=self.room,
            paid_by=self.guest_user,
            paid_for_tuple=(self.user,),
            parent_transaction_kwargs={"currency": currency},
            child_transaction_kwargs={"value": Decimal(5)},
        )

        self.assertEqual(self.guest_user.debts.count(), 1)
        guest_user_debt = self.guest_user.debts.first()
        self.assertEqual(guest_user_debt.value, Decimal(5))
        self.assertEqual(guest_user_debt.creditor, self.user)

        self.assertEqual(self.user.debts.count(), 0)

    def test_complicated_reduction(self):
        currency = baker.make_recipe("apps.currency.tests.currency")

        user_list = baker.make_recipe("apps.account.tests.user", _quantity=2)
        guest_user_list = baker.make_recipe("apps.account.tests.guest_user", _quantity=2)

        default_kwargs = {"room": self.room, "parent_transaction_kwargs": {{"currency": currency}}}

        self.room.users.add(*user_list + guest_user_list)

        user_1 = self.user
        user_2 = user_list[0]
        user_3 = user_list[1]
        guest_user_1 = self.guest_user
        guest_user_2 = guest_user_list[0]
        guest_user_3 = guest_user_list[1]

        create_parent_transaction_with_optimisation(
            **default_kwargs,
            paid_by=user_1,
            paid_for_tuple=(user_1, user_2, guest_user_1),
            child_transaction_kwargs={"value": Decimal(10)},
        )

        create_parent_transaction_with_optimisation(
            **default_kwargs,
            paid_by=guest_user_1,
            paid_for_tuple=(
                guest_user_1,
                user_2,
            ),
            child_transaction_kwargs={"value": Decimal(5)},
        )
