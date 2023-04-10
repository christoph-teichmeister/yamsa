from _decimal import Decimal
from django.urls import reverse
from model_bakery import baker

from apps.core.tests.setup import BaseTestSetUp
from apps.moneyflow.models import MoneyFlow
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
            **base_data,
            paid_for=(self.guest_user_2.id,),
            paid_by=self.guest_user_1,
            value=Decimal(10)
        )

        self.create_transaction(
            **base_data,
            paid_for=(self.guest_user_3.id,),
            paid_by=self.guest_user_2,
            value=Decimal(5)
        )

        self.create_transaction(
            **base_data,
            paid_for=(self.guest_user_1.id,),
            paid_by=self.guest_user_3,
            value=Decimal(5)
        )

        response = self.client.get(reverse("room-detail", args=(self.room.id,)))

        print(response)

        self.assertEqual(self.guest_user_1.money_flows.first().incoming, Decimal(5))
        self.assertEqual(self.guest_user_1.money_flows.first().outgoing, Decimal(0))

        self.assertEqual(self.guest_user_2.money_flows.first().incoming, Decimal(0))
        self.assertEqual(self.guest_user_2.money_flows.first().outgoing, Decimal(5))

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
            **base_data,
            paid_by=self.guest_user_1,
            paid_for=(self.guest_user_2.id,),
            value=Decimal(1)
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
            **base_data,
            paid_by=self.guest_user_3,
            paid_for=(self.guest_user_2.id,),
            value=Decimal(5)
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
            **base_data,
            paid_by=self.guest_user_1,
            paid_for=(self.guest_user_3.id,),
            value=Decimal(8)
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
            **base_data,
            paid_by=self.guest_user_3,
            paid_for=(self.guest_user_2.id,),
            value=Decimal(10)
        )
        self.assertEqual(self.guest_user_3.money_flows.first().incoming, Decimal(0.5))
        self.assertEqual(self.guest_user_3.money_flows.first().outgoing, Decimal(0))

        self.assertEqual(self.guest_user_2.money_flows.first().incoming, Decimal(0))
        self.assertEqual(self.guest_user_2.money_flows.first().outgoing, Decimal(11.5))

        response = self.client.get(reverse("room-detail", args=(self.room.id,)))

        print(response)
        print([e for e in response.context_data["shit_qs"]])

        # Final Assertions after everything has been done

        self.assertEqual(
            MoneyFlow.objects.get(user_id=self.guest_user_1).incoming, Decimal(11)
        )
        self.assertEqual(
            MoneyFlow.objects.get(user_id=self.guest_user_1).outgoing, Decimal(0)
        )

        self.assertEqual(
            MoneyFlow.objects.get(user_id=self.guest_user_2).incoming, Decimal(0)
        )
        self.assertEqual(
            MoneyFlow.objects.get(user_id=self.guest_user_2).outgoing, Decimal(11.5)
        )

        self.assertEqual(
            MoneyFlow.objects.get(user_id=self.guest_user_3).incoming, Decimal(0.5)
        )
        self.assertEqual(
            MoneyFlow.objects.get(user_id=self.guest_user_3).outgoing, Decimal(0)
        )

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
