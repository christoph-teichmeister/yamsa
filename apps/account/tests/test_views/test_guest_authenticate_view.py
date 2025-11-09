import http

from django.urls import reverse

from apps.core.tests.setup import BaseTestSetUp
from apps.transaction.views import TransactionListView


class AuthenticateGuestUserViewTestCase(BaseTestSetUp):
    def test_post_as_anonymous_user(self):
        self.client.logout()
        response = self.client.post(
            reverse("account:guest-login"),
            data={"room_slug": self.room.slug, "user_id": self.guest_user.id},
            follow=True,
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        # Assert that we've been redirected to the transaction list view
        self.assertEqual(response.template_name[0], TransactionListView.template_name)
        self.assertIn("Room transactions", str(response.content))

    def test_post_as_registered_user(self):
        client = self.reauthenticate_user(self.user)
        response = client.post(
            reverse("account:guest-login"),
            data={"room_slug": self.room.slug, "user_id": self.user.id},
            follow=True,
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        # Assert that we've been redirected to the transaction list view
        self.assertEqual(response.template_name[0], TransactionListView.template_name)
        self.assertIn("Room transactions", str(response.content))
