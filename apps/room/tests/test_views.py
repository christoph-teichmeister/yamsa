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
            **base_data,
            description="user 1 10€ for user 2",
            paid_for=(self.guest_user_2.id,),
            paid_by=self.guest_user_1,
            value=Decimal(10)
        )

        self.create_transaction(
            **base_data,
            description="user 2 5€ for user 3",
            paid_for=(self.guest_user_3.id,),
            paid_by=self.guest_user_2,
            value=Decimal(5)
        )

        self.create_transaction(
            **base_data,
            description="user 3 5€ for user 1",
            paid_for=(self.guest_user_1.id,),
            paid_by=self.guest_user_3,
            value=Decimal(5)
        )

        response = self.client.get(reverse("room-detail", args=(self.room.id,)))

        print(response)

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

        self.create_transaction(
            **base_data,
            paid_by=self.guest_user_2,
            paid_for=(self.guest_user_2.id, self.guest_user_3.id),
            value=Decimal(5)
        )

        self.create_transaction(
            **base_data,
            paid_by=self.guest_user_3,
            paid_for=(self.guest_user_2.id,),
            value=Decimal(5)
        )

        self.create_transaction(
            **base_data,
            paid_by=self.guest_user_2,
            paid_for=(self.guest_user_2.id, self.guest_user_3.id),
            value=Decimal(6)
        )

        self.create_transaction(
            **base_data,
            paid_by=self.guest_user_1,
            paid_for=(self.guest_user_3.id,),
            value=Decimal(8)
        )

        self.create_transaction(
            **base_data,
            paid_by=self.guest_user_1,
            paid_for=(self.guest_user_1.id, self.guest_user_2.id, self.guest_user_3.id),
            value=Decimal(3)
        )

        self.create_transaction(
            **base_data,
            paid_by=self.guest_user_3,
            paid_for=(self.guest_user_2.id,),
            value=Decimal(10)
        )

        response = self.client.get(reverse("room-detail", args=(self.room.id,)))

        print(response)
        print([e for e in response.context_data["shit_qs"]])
