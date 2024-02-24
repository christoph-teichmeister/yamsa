import http

from django.urls import reverse
from model_bakery import baker

from apps.core.tests.setup import BaseTestSetUp
from apps.transaction.views import TransactionListView


class AuthenticateGuestUserViewTestCase(BaseTestSetUp):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.room = baker.make_recipe("apps.room.tests.room")

    def test_post_as_guest(self):
        self.room.users.add(self.guest_user)

        self.client.logout()
        response = self.client.post(
            reverse("account:guest-login"),
            data={"room_slug": self.room.slug, "user_id": self.guest_user.id},
            follow=True,
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        # Assert, that we've been redirected to the transaction list view
        self.assertTrue(response.template_name[0], TransactionListView.template_name)
        self.assertIn("Transactions made", str(response.content))

    def test_post_as_registered_user(self):
        self.room.users.add(self.user)

        client = self.reauthenticate_user(self.user)
        response = client.post(
            reverse("account:guest-login"),
            data={"room_slug": self.room.slug, "user_id": self.user.id},
            follow=True,
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        # Assert, that we've been redirected to the transaction list view
        self.assertTrue(response.template_name[0], TransactionListView.template_name)
        self.assertIn("Transactions made", str(response.content))
