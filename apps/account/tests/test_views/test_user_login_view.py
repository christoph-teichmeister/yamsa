import http

from django.conf import settings
from django.urls import reverse

from apps.account.constants import SESSION_TTL_SESSION_KEY
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
        self.assertIn("Create an account", stringed_content)
        self.assertIn("Welcome back", stringed_content)

    def test_post_regular(self):
        self.client.logout()
        response = self.client.post(
            reverse("account:login"), data={"email": self.user.email, "password": default_password}, follow=True
        )

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], WelcomePartialView.template_name)
        self.assertEqual(settings.SESSION_COOKIE_AGE, self.client.session[SESSION_TTL_SESSION_KEY])
        self.assertEqual(settings.SESSION_COOKIE_AGE, self.client.session.get_expiry_age())

    def test_post_email_and_password_are_required(self):
        self.client.logout()
        response = self.client.post(reverse("account:login"))

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        stringed_content = str(response.content)

        self.assertIn("This field is required", stringed_content)
        self.assertGreaterEqual(stringed_content.count("This field is required"), 2)

    def test_post_with_remember_me_extends_session(self):
        self.client.logout()

        response = self.client.post(
            reverse("account:login"),
            data={"email": self.user.email, "password": default_password, "remember_me": "on"},
            follow=True,
        )

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(settings.DJANGO_REMEMBER_ME_SESSION_AGE, self.client.session.get_expiry_age())
        self.assertEqual(settings.DJANGO_REMEMBER_ME_SESSION_AGE, self.client.session[SESSION_TTL_SESSION_KEY])

    def test_post_email_and_password_do_not_match(self):
        self.client.logout()

        # Wrong password
        response = self.client.post(
            reverse("account:login"), data={"email": self.user.email, "password": "wrong_password"}
        )

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], LogInUserView.template_name)

        self.assertIn(str(LogInUserView.ExceptionMessage.AUTH_FAILED), str(response.content))

        # Wrong email
        response = self.client.post(
            reverse("account:login"), data={"email": f"{self.user.email}-wrong", "password": default_password}
        )

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], LogInUserView.template_name)

        self.assertIn(str(LogInUserView.ExceptionMessage.AUTH_FAILED), str(response.content))
