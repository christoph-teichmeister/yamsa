from apps.account.forms.user_forgot_password_form import UserForgotPasswordForm
from apps.core.tests.setup import BaseTestSetUp


class UserForgotPasswordFormTestCase(BaseTestSetUp):
    form = UserForgotPasswordForm

    def test_regular(self):
        form = self.form(data={"email": self.user.email})
        self.assertTrue(form.is_valid())

    def test_form_raises_error_if_email_is_unknown(self):
        unknown_email = "unknown_email@local.local"
        form = self.form(data={"email": unknown_email})
        self.assertFalse(form.is_valid())

        self.assertEqual(
            form.errors["email"][0], form.ExceptionMessage.UNKNOWN_EMAIL_ADDRESS.format(email=unknown_email)
        )
