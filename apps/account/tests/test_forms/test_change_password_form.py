import pytest
from django.contrib.auth import authenticate

from apps.account.forms.change_password_form import ChangePasswordForm
from apps.account.tests.constants import DEFAULT_PASSWORD

pytestmark = pytest.mark.django_db


class TestChangePasswordForm:
    def test_regular(self, user, form_request):
        new_password = "new_password"

        form = ChangePasswordForm(
            request=form_request,
            instance=user,
            data={
                "id": user.id,
                "old_password": DEFAULT_PASSWORD,
                "new_password": new_password,
                "new_password_confirmation": new_password,
            },
        )
        assert form.is_valid()

        form.save()
        user.refresh_from_db()

        authenticated_user = authenticate(request=form_request, email=user.email, password=new_password)
        assert authenticated_user == user

    def test_password_incorrect(self, user, form_request):
        form = ChangePasswordForm(
            request=form_request,
            instance=user,
            data={
                "id": user.id,
                "old_password": "an_incorrect_password",
                "new_password": "some_password",
                "new_password_confirmation": "some_password",
            },
        )
        assert not form.is_valid()
        assert form.errors["old_password"][0] == form.ExceptionMessage.PASSWORD_INCORRECT

    def test_new_passwords_do_not_match(self, user, form_request):
        form = ChangePasswordForm(
            request=form_request,
            instance=user,
            data={
                "id": user.id,
                "old_password": DEFAULT_PASSWORD,
                "new_password": "1",
                "new_password_confirmation": "2",
            },
        )
        assert not form.is_valid()
        assert form.errors["new_password_confirmation"][0] == form.ExceptionMessage.PASSWORDS_DO_NOT_MATCH
