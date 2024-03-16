import http

from django.urls import reverse

from apps.account.tests.baker_recipes import default_password
from apps.account.views import LogInUserView
from apps.core.tests.setup import BaseTestSetUp
from apps.core.views import WelcomePartialView


class LogInUserViewTestCase(BaseTestSetUp):
    def test_get_regular(self):
        self.client.logout()
        response = self.client.get(reverse("account:login"))

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], LogInUserView.template_name)

        stringed_content = str(response.content)
        self.assertIn("Login", stringed_content)
        self.assertIn("Forgot password?", stringed_content)

        self.assertIn("have an account yet?", stringed_content)
        self.assertIn("Register here!", stringed_content)

    def test_post_regular(self):
        self.client.logout()
        response = self.client.post(
            reverse("account:login"), data={"username": self.user.username, "password": default_password}, follow=True
        )

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], WelcomePartialView.template_name)

    def test_post_username_and_password_are_required(self):
        self.client.logout()
        response = self.client.post(reverse("account:login"))

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], WelcomePartialView.template_name)

        stringed_content = str(response.content)

        self.assertIn("passwordError", stringed_content)
        self.assertIn("usernameError", stringed_content)
        self.assertIn("This field is required", stringed_content)

    def test_post_username_and_password_do_not_match(self):
        self.client.logout()

        # Wrong password
        response = self.client.post(
            reverse("account:login"), data={"username": self.user.username, "password": "wrong_password"}
        )

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], LogInUserView.template_name)

        self.assertIn(LogInUserView.ExceptionMessage.AUTH_FAILED, str(response.content))

        # Wrong username
        response = self.client.post(
            reverse("account:login"), data={"username": f"{self.user.username}-wrong", "password": default_password}
        )

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], LogInUserView.template_name)

        self.assertIn(LogInUserView.ExceptionMessage.AUTH_FAILED, str(response.content))
