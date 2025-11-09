import http

from django.urls import reverse

from apps.account.views import UserDetailView, UserUpdateView
from apps.core.tests.setup import BaseTestSetUp


class UserUpdateViewTestCase(BaseTestSetUp):
    def test_get_regular(self):
        client = self.reauthenticate_user(self.user)
        response = client.get(reverse("account:update", kwargs={"pk": self.user.id}))
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertTrue(response.template_name[0], UserUpdateView.template_name)

        stringed_content = response.content.decode()

        self.assertIn("Keep your details up to date", stringed_content)
        self.assertIn("Need a new password?", stringed_content)

    def test_post_regular(self):
        new_name = "new_name"

        client = self.reauthenticate_user(self.user)
        response = client.post(
            reverse("account:update", kwargs={"pk": self.user.id}),
            data={"name": new_name, "email": self.user.email},
            follow=True,
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertTrue(response.template_name[0], UserDetailView.template_name)

        stringed_content = response.content.decode()

        self.assertIn("Your account overview", stringed_content)
        self.assertIn("Edit profile", stringed_content)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, new_name)
