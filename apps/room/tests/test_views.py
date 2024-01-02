from _decimal import Decimal

from django.urls import reverse
from model_bakery import baker

from apps.core.tests.setup import BaseTestSetUp
from apps.transaction import views
from apps.transaction.tests.helpers import TransactionHelpersMixin


class RoomDetailViewTestCase(TransactionHelpersMixin, BaseTestSetUp):
    view_class = views.TransactionCreateView

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.guest_user_1 = baker.make_recipe("apps.account.tests.guest_user")
        cls.guest_user_2 = baker.make_recipe("apps.account.tests.guest_user")
        cls.guest_user_3 = baker.make_recipe("apps.account.tests.guest_user")
        cls.room = baker.make_recipe("apps.room.tests.room")

    def test_simple_test_case(self):
        """
        User 1 pays 10 € for User 2
        User 2 pays 5 € for User 3
        User 3 pays 5 € for User 1

        => User 2 pays 5€ to User 1 and that's it
        """

        base_data = {"room": self.room}
        self.create_transaction(
            **base_data, paid_for=(self.guest_user_2.id,), paid_by=self.guest_user_1, value=Decimal(10)
        )

        self.create_transaction(
            **base_data, paid_for=(self.guest_user_3.id,), paid_by=self.guest_user_2, value=Decimal(5)
        )

        self.create_transaction(
            **base_data, paid_for=(self.guest_user_1.id,), paid_by=self.guest_user_3, value=Decimal(5)
        )

        self.assertEqual(self.guest_user_1.money_flows.first().incoming, Decimal(5))
        self.assertEqual(self.guest_user_1.money_flows.first().outgoing, Decimal(0))

        self.assertEqual(self.guest_user_2.money_flows.first().incoming, Decimal(0))
        self.assertEqual(self.guest_user_2.money_flows.first().outgoing, Decimal(5))

        res = self.client.get(reverse("room:dashboard", kwargs={"room_slug": self.room.slug}))
        print(res)

    def test_simple_test_case_2(self):
        """
        User 1 pays 1 € for User 2
        User 2 pays 5 € for User 2, 3
        User 3 pays 5 € for User 2
        User 2 pays 6 € for User 2, 3
        User 1 pays 8 € for User 3
        User 1 pays 3 € for User 1, 2, 3
        User 3 pays 10 € for User 2

        User 2 pays 11€ to User 1
        User 2 pays 0,5€ to User 3
        """

        base_data = {"room": self.room}
        self.create_transaction(
            **base_data, paid_by=self.guest_user_1, paid_for=(self.guest_user_2.id,), value=Decimal(1)
        )
        self.assertEqual(self.guest_user_1.money_flows.first().incoming, Decimal(1))
        self.assertEqual(self.guest_user_1.money_flows.first().outgoing, Decimal(0))

        self.assertEqual(self.guest_user_2.money_flows.first().incoming, Decimal(0))
        self.assertEqual(self.guest_user_2.money_flows.first().outgoing, Decimal(1))

        self.create_transaction(
            **base_data,
            paid_by=self.guest_user_2,
            paid_for=(self.guest_user_2.id, self.guest_user_3.id),
            value=Decimal(5)
        )
        self.assertEqual(self.guest_user_2.money_flows.first().incoming, Decimal(1.5))
        self.assertEqual(self.guest_user_2.money_flows.first().outgoing, Decimal(0))

        self.assertEqual(self.guest_user_3.money_flows.first().incoming, Decimal(0))
        self.assertEqual(self.guest_user_3.money_flows.first().outgoing, Decimal(2.5))

        self.create_transaction(
            **base_data, paid_by=self.guest_user_3, paid_for=(self.guest_user_2.id,), value=Decimal(5)
        )
        self.assertEqual(self.guest_user_3.money_flows.first().incoming, Decimal(2.5))
        self.assertEqual(self.guest_user_3.money_flows.first().outgoing, Decimal(0))

        self.assertEqual(self.guest_user_2.money_flows.first().incoming, Decimal(0))
        self.assertEqual(self.guest_user_2.money_flows.first().outgoing, Decimal(3.5))

        self.create_transaction(
            **base_data,
            paid_by=self.guest_user_2,
            paid_for=(self.guest_user_2.id, self.guest_user_3.id),
            value=Decimal(6)
        )
        self.assertEqual(self.guest_user_2.money_flows.first().incoming, Decimal(0))
        self.assertEqual(self.guest_user_2.money_flows.first().outgoing, Decimal(0.5))

        self.assertEqual(self.guest_user_3.money_flows.first().incoming, Decimal(0))
        self.assertEqual(self.guest_user_3.money_flows.first().outgoing, Decimal(0.5))

        self.create_transaction(
            **base_data, paid_by=self.guest_user_1, paid_for=(self.guest_user_3.id,), value=Decimal(8)
        )
        self.assertEqual(self.guest_user_1.money_flows.first().incoming, Decimal(9))
        self.assertEqual(self.guest_user_1.money_flows.first().outgoing, Decimal(0))

        self.assertEqual(self.guest_user_3.money_flows.first().incoming, Decimal(0))
        self.assertEqual(self.guest_user_3.money_flows.first().outgoing, Decimal(8.5))

        self.create_transaction(
            **base_data,
            paid_by=self.guest_user_1,
            paid_for=(self.guest_user_1.id, self.guest_user_2.id, self.guest_user_3.id),
            value=Decimal(3)
        )
        self.assertEqual(self.guest_user_1.money_flows.first().incoming, Decimal(11))
        self.assertEqual(self.guest_user_1.money_flows.first().outgoing, Decimal(0))

        self.assertEqual(self.guest_user_2.money_flows.first().incoming, Decimal(0))
        self.assertEqual(self.guest_user_2.money_flows.first().outgoing, Decimal(1.5))

        self.assertEqual(self.guest_user_3.money_flows.first().incoming, Decimal(0))
        self.assertEqual(self.guest_user_3.money_flows.first().outgoing, Decimal(9.5))

        self.create_transaction(
            **base_data, paid_by=self.guest_user_3, paid_for=(self.guest_user_2.id,), value=Decimal(10)
        )
        self.assertEqual(self.guest_user_3.money_flows.first().incoming, Decimal(0.5))
        self.assertEqual(self.guest_user_3.money_flows.first().outgoing, Decimal(0))

        self.assertEqual(self.guest_user_2.money_flows.first().incoming, Decimal(0))
        self.assertEqual(self.guest_user_2.money_flows.first().outgoing, Decimal(11.5))

        # Final Assertions after everything has been done

        # self.assertEqual(
        #     MoneyFlow.objects.get(user_id=self.guest_user_1).incoming, Decimal(11)
        # )
        # self.assertEqual(
        #     MoneyFlow.objects.get(user_id=self.guest_user_1).outgoing, Decimal(0)
        # )

        # self.assertEqual(
        #     MoneyFlow.objects.get(user_id=self.guest_user_2).incoming, Decimal(0)
        # )
        # self.assertEqual(
        #     MoneyFlow.objects.get(user_id=self.guest_user_2).outgoing, Decimal(11.5)
        # )

        # self.assertEqual(
        #     MoneyFlow.objects.get(user_id=self.guest_user_3).incoming, Decimal(0.5)
        # )
        # self.assertEqual(
        #     MoneyFlow.objects.get(user_id=self.guest_user_3).outgoing, Decimal(0)
        # )

    def test_simple_test_case_3(self):
        """
        User 1 pays 10 € for User 2, 3
        User 1 pays 10 € for User 1, 2, 5
        User 4 pays 20 € for User 1, 2
        User 4 pays 20 € for User 1, 2
        User 4 pays 20 € for User 1, 2
        User 4 pays 20 € for User 1, 3, 4

        =>  User 4 receives 73,37 €
            User 1 pays 20 € to User 4
            All the others pay anyway
        """

        self.guest_user_4 = baker.make_recipe("apps.account.tests.guest_user")
        self.guest_user_5 = baker.make_recipe("apps.account.tests.guest_user")

        base_data = {"room": self.room}
        self.create_transaction(
            **base_data,
            paid_by=self.guest_user_1,
            paid_for=(
                self.guest_user_2.id,
                self.guest_user_3.id,
            ),
            value=Decimal(10)
        )
        self.assert_money_flow_values(user=self.guest_user_1, incoming=10, outgoing=0)
        self.assert_money_flow_values(user=self.guest_user_2, incoming=0, outgoing=5)
        self.assert_money_flow_values(user=self.guest_user_3, incoming=0, outgoing=5)

        self.create_transaction(
            **base_data,
            paid_by=self.guest_user_1,
            paid_for=(self.guest_user_1.id, self.guest_user_2.id, self.guest_user_5.id),
            value=Decimal(10)
        )
        self.assert_money_flow_values(user=self.guest_user_1, incoming=16.66, outgoing=0)
        self.assert_money_flow_values(user=self.guest_user_2, incoming=0, outgoing=8.33)
        self.assert_money_flow_values(user=self.guest_user_5, incoming=0, outgoing=3.33)

        self.create_transaction(
            **base_data,
            paid_by=self.guest_user_4,
            paid_for=(
                self.guest_user_1.id,
                self.guest_user_2.id,
            ),
            value=Decimal(20)
        )
        self.assert_money_flow_values(user=self.guest_user_4, incoming=20, outgoing=0)
        self.assert_money_flow_values(user=self.guest_user_1, incoming=6.66, outgoing=0)
        self.assert_money_flow_values(user=self.guest_user_2, incoming=0, outgoing=18.33)

        self.create_transaction(
            **base_data,
            paid_by=self.guest_user_4,
            paid_for=(
                self.guest_user_1.id,
                self.guest_user_2.id,
            ),
            value=Decimal(20)
        )
        self.assert_money_flow_values(user=self.guest_user_4, incoming=40, outgoing=0)
        self.assert_money_flow_values(user=self.guest_user_1, incoming=0, outgoing=3.34)
        self.assert_money_flow_values(user=self.guest_user_2, incoming=0, outgoing=28.33)

        self.create_transaction(
            **base_data,
            paid_by=self.guest_user_4,
            paid_for=(
                self.guest_user_1.id,
                self.guest_user_2.id,
            ),
            value=Decimal(20)
        )
        self.assert_money_flow_values(user=self.guest_user_4, incoming=60, outgoing=0)
        self.assert_money_flow_values(user=self.guest_user_1, incoming=0, outgoing=13.34)
        self.assert_money_flow_values(user=self.guest_user_2, incoming=0, outgoing=38.33)

        self.create_transaction(
            **base_data,
            paid_by=self.guest_user_4,
            paid_for=(
                self.guest_user_1.id,
                self.guest_user_3.id,
                self.guest_user_4.id,
            ),
            value=Decimal(20)
        )
        self.assert_money_flow_values(user=self.guest_user_4, incoming=73.34, outgoing=0)
        self.assert_money_flow_values(user=self.guest_user_1, incoming=0, outgoing=20.01)
        self.assert_money_flow_values(user=self.guest_user_3, incoming=0, outgoing=11.67)

        # Final Assertions after everything has been done

        self.assert_money_flow_values(user=self.guest_user_1, incoming=0, outgoing=20.01)
        self.assert_money_flow_values(user=self.guest_user_2, incoming=0, outgoing=38.33)
        self.assert_money_flow_values(user=self.guest_user_3, incoming=0, outgoing=11.67)
        self.assert_money_flow_values(user=self.guest_user_4, incoming=73.34, outgoing=0)
        self.assert_money_flow_values(user=self.guest_user_5, incoming=0, outgoing=3.33)

    def test_money_flow_creation_on_transaction_creation(self):
        base_data = {"room": self.room}
        self.create_transaction(
            **base_data,
            paid_by=self.guest_user_1,
            paid_for=(
                self.guest_user_2.id,
                self.guest_user_3.id,
            ),
            value=Decimal(10)
        )

        self.assertEqual(self.guest_user_1.money_flows.first().incoming, Decimal(10))
