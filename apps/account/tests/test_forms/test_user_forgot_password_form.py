import pytest

from apps.account.forms.user_forgot_password_form import UserForgotPasswordForm


@pytest.mark.django_db
class TestUserForgotPasswordForm:
    form_class = UserForgotPasswordForm

    def test_regular(self, user):
        form = self.form_class(data={"email": user.email})
        assert form.is_valid()

    def test_form_raises_error_if_email_is_unknown(self):
        unknown_email = "unknown_email@local.local"
        form = self.form_class(data={"email": unknown_email})
        assert not form.is_valid()

        assert form.errors["email"][0] == form.ExceptionMessage.UNKNOWN_EMAIL_ADDRESS.format(email=unknown_email)
