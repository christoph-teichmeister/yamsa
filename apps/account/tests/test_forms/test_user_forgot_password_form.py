import pytest

from apps.account.forms.user_forgot_password_form import UserForgotPasswordForm
from apps.account.models import User


@pytest.mark.django_db
class TestUserForgotPasswordForm:
    form_class = UserForgotPasswordForm

    def test_regular(self, user: User) -> None:
        form = self.form_class(data={"email": user.email})
        assert form.is_valid()

    def test_unknown_email_is_valid_so_the_form_does_not_reveal_registrations(self) -> None:
        form = self.form_class(data={"email": "unknown_email@local.local"})
        assert form.is_valid()
