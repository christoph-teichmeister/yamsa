import http

from django.urls import reverse

from apps.account.views import UserDetailView
from apps.core.tests.setup import BaseTestSetUp


class UserDetailViewTestCase(BaseTestSetUp):
    def test_get_as_registered_user_own_profile(self):
        self.user.paypal_me_username = "paypal_username"
        self.user.save()

        client = self.reauthenticate_user(self.user)
        response = client.get(reverse("account:detail", args=(self.user.id,)))

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], UserDetailView.template_name)

        stringed_content = str(response.content).replace("\\n", "")
        self.assertInHTML("Your data:", stringed_content)
        self.assertIn(self.user.name, stringed_content)
        self.assertIn(self.user.email, stringed_content)
        self.assertIn(f"@{self.user.paypal_me_username}", stringed_content)

        self.assertNotIn('id="superuser-admin-link"', stringed_content)

    def test_get_as_registered_user_other_profile_of_room(self):
        self.room.users.add(self.superuser)

        client = self.reauthenticate_user(self.user)
        response = client.get(reverse("account:detail", args=(self.superuser.id,)))

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], UserDetailView.template_name)

        stringed_content = str(response.content).replace("\\n", "")
        self.assertInHTML("Their data:", stringed_content)
        self.assertIn(self.superuser.name, stringed_content)
        self.assertIn(self.superuser.email, stringed_content)

        self.assertNotIn('id="superuser-admin-link"', stringed_content)

    def test_get_as_registered_user_other_profile_who_is_not_in_room(self):
        """This can only happen if someone edits the URL"""
        client = self.reauthenticate_user(self.user)
        response = client.get(reverse("account:detail", args=(self.superuser.id,)))

        self.assertEqual(response.status_code, http.HTTPStatus.FORBIDDEN)

        stringed_content = str(response.content).replace("\n", "")
        self.assertIn("You are not allowed", stringed_content)
        self.assertIn("to see this page", stringed_content)

    def test_get_as_guest_own_profile(self):
        self.client.force_login(self.guest_user)
        response = self.client.get(reverse("account:detail", args=(self.guest_user.id,)))

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], UserDetailView.template_name)

        stringed_content = str(response.content)
        self.assertIn("- You are a guest -", stringed_content)
        self.assertIn(f"Thank you for using yamsa, {self.guest_user.name}!", stringed_content)

        self.assertNotIn('id="superuser-admin-link"', stringed_content)

    def test_get_as_guest_other_profile(self):
        self.user.paypal_me_username = "paypal_username"
        self.user.save()

        self.client.force_login(self.guest_user)
        response = self.client.get(reverse("account:detail", args=(self.user.id,)))

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], UserDetailView.template_name)

        stringed_content = str(response.content).replace("\\n", "")
        self.assertInHTML("Their data:", stringed_content)
        self.assertIn(self.user.name, stringed_content)
        self.assertIn(self.user.email, stringed_content)
        self.assertIn(f"@{self.user.paypal_me_username}", stringed_content)

        self.assertNotIn('id="superuser-admin-link"', stringed_content)

    def test_get_as_superuser_own_profile(self):
        client = self.reauthenticate_user(self.superuser)
        response = client.get(reverse("account:detail", args=(self.superuser.id,)))

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], UserDetailView.template_name)

        stringed_content = str(response.content).replace("\\n", "")
        self.assertInHTML("Your data:", stringed_content)
        self.assertIn(self.superuser.name, stringed_content)
        self.assertIn(self.superuser.email, stringed_content)

        self.assertIn('id="superuser-admin-link"', stringed_content, f"{stringed_content=}")

    def test_get_as_superuser_other_profile(self):
        self.assertFalse(
            self.superuser.rooms.all().exists(), "This test does not make sense, if the superuser belongs to a room"
        )

        client = self.reauthenticate_user(self.superuser)
        response = client.get(reverse("account:detail", args=(self.user.id,)))

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], UserDetailView.template_name)

        stringed_content = str(response.content).replace("\\n", "")
        self.assertInHTML("Their data:", stringed_content)
        self.assertIn(self.user.name, stringed_content)
        self.assertIn(self.user.email, stringed_content)

        self.assertNotIn('id="superuser-admin-link"', stringed_content)
