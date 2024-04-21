import http
from unittest import mock

from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from apps.account.forms.user_forgot_password_form import UserForgotPasswordForm
from apps.account.messages.commands.send_post_register_email import SendPostRegisterEmail
from apps.account.views import RegisterUserView
from apps.core.tests.setup import BaseTestSetUp
from apps.core.views import WelcomePartialView


class RegisterUserViewTestCase(BaseTestSetUp):
    def test_get_regular(self):
        self.client.logout()
        response = self.client.get(reverse("account:register"))
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertTrue(response.template_name[0], RegisterUserView.template_name)
        self.assertIn("Register", str(response.content))

        self.assertIn("Already have an account?", str(response.content))
        self.assertIn("Login here!", str(response.content))

    def test_get_from_invitation_email(self):
        email_from_invitation_email = "invitation@local.local"

        self.client.logout()
        response = self.client.get(
            f'{reverse("account:register")}?with_email={email_from_invitation_email}&for_guest={self.guest_user.id}'
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertTrue(response.template_name[0], RegisterUserView.template_name)

        self.assertEqual(response.context_data["email_from_invitation_email"], email_from_invitation_email)
        self.assertEqual(response.context_data["form"].initial["email"], email_from_invitation_email)
        self.assertEqual(response.context_data["form"].initial["id"], str(self.guest_user.id))

        self.assertIn("Register", str(response.content))

        self.assertIn("Already have an account?", str(response.content))
        self.assertIn("Login here!", str(response.content))

    def test_post_regular(self):
        new_name = "new_name"
        new_email = "new_email@local.local"
        new_password = "a_password"

        self.client.logout()

        with mock.patch("apps.account.views.user_register_view.handle_message") as mocked_handle_message:
            response = self.client.post(
                reverse("account:register"),
                data={"name": new_name, "email": new_email, "password": new_password},
                follow=True,
            )
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

            mocked_handle_message.assert_called_once()
            self.assertIsInstance(mocked_handle_message.call_args[0][0], SendPostRegisterEmail)

        self.assertTrue(response.template_name[0], WelcomePartialView.template_name)

        self.assertNotIsInstance(response.wsgi_request.user, AnonymousUser)
        self.assertEqual(response.wsgi_request.user.name, new_name)
        self.assertEqual(response.wsgi_request.user.email, new_email)

    def test_post_from_invitation_email(self):
        guest_name = "guest_name"
        guest_email = "guest_email@local.local"
        guest_password = "guest_password"

        self.client.logout()

        with mock.patch("apps.account.views.user_register_view.handle_message") as mocked_handle_message:
            response = self.client.post(
                reverse("account:register"),
                data={
                    "id": self.guest_user.id,
                    "name": guest_name,
                    "email": guest_email,
                    "password": guest_password,
                },
                follow=True,
            )
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

            mocked_handle_message.assert_called_once()
            self.assertIsInstance(mocked_handle_message.call_args[0][0], SendPostRegisterEmail)

        self.assertTrue(response.template_name[0], WelcomePartialView.template_name)

        self.assertNotIsInstance(response.wsgi_request.user, AnonymousUser)
        self.assertEqual(response.wsgi_request.user.name, guest_name)
        self.assertEqual(response.wsgi_request.user.email, guest_email)

        self.guest_user.refresh_from_db()

        self.assertFalse(self.guest_user.is_guest)

    def test_post_email_invalid(self):
        self.client.logout()

        response = self.client.post(reverse("account:register"))
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertTrue(response.template_name[0], UserForgotPasswordForm.template_name)

        stringed_content = str(response.content)

        self.assertIn('id="emailError"', stringed_content)
        self.assertIn('id="passwordError"', stringed_content)
        self.assertIn('id="nameError"', stringed_content)
