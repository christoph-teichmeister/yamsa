import http
from unittest import mock

from django.urls import reverse

from apps.account.forms.user_forgot_password_form import UserForgotPasswordForm
from apps.account.messages.commands.send_forgot_password_email import SendForgotPasswordEmail
from apps.account.views import LogInUserView, UserForgotPasswordView
from apps.core.tests.setup import BaseTestSetUp


class UserForgotPasswordViewTestCase(BaseTestSetUp):
    def test_get_regular(self):
        client = self.reauthenticate_user(self.user)
        response = client.get(reverse("account:forgot-password"))
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertTrue(response.template_name[0], UserForgotPasswordView.template_name)
        self.assertIn("Forgot Password", str(response.content))

    def test_post_regular(self):
        client = self.reauthenticate_user(self.user)

        with mock.patch("apps.account.views.user_forgot_password_view.handle_message") as mocked_handle_message:
            response = client.post(
                reverse("account:forgot-password"),
                data={"email": self.user.email},
                follow=True,
            )
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

            mocked_handle_message.assert_called_once()
            self.assertIsInstance(mocked_handle_message.call_args[0][0], SendForgotPasswordEmail)

        self.assertTrue(response.template_name[0], LogInUserView.template_name)
        self.assertIn("Login", str(response.content))

    def test_post_email_invalid(self):
        unknown_email = "unknown_email@local.local"

        client = self.reauthenticate_user(self.user)

        response = client.post(
            reverse("account:forgot-password"),
            data={"email": unknown_email},
            follow=True,
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertTrue(response.template_name[0], UserForgotPasswordForm.template_name)
        self.assertIn('id="emailError"', str(response.content))
        self.assertIn(
            f"The email address &#x27;{unknown_email}&#x27; is not registered with yamsa",
            str(response.content),
        )
