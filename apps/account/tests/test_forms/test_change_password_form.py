from django.contrib.auth import authenticate

from apps.account.forms.change_password_form import ChangePasswordForm
from apps.account.tests.baker_recipes import default_password
from apps.core.tests.setup import BaseTestSetUp


class ChangePasswordFormTestCase(BaseTestSetUp):
    form = ChangePasswordForm

    def test_regular(self):
        new_password = "new_password"

        form = self.form(
            instance=self.user,
            data={
                "id": self.user.id,
                "old_password": default_password,
                "new_password": new_password,
                "new_password_confirmation": new_password,
            },
        )
        self.assertTrue(form.is_valid())

        form.save()
        self.user.refresh_from_db()

        user = authenticate(username=self.user.username, password=new_password)
        self.assertEqual(user, self.user)

    def test_password_incorrect(self):
        form = self.form(
            instance=self.user,
            data={
                "id": self.user.id,
                "old_password": "an_incorrect_password",
                "new_password": "some_password",
                "new_password_confirmation": "some_password",
            },
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["old_password"][0], form.ExceptionMessage.PASSWORD_INCORRECT, form.errors)

    def test_new_passwords_do_not_match(self):
        form = self.form(
            instance=self.user,
            data={
                "id": self.user.id,
                "old_password": default_password,
                "new_password": "1",
                "new_password_confirmation": "2",
            },
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["new_password_confirmation"][0], form.ExceptionMessage.PASSWORDS_DO_NOT_MATCH, form.errors
        )
