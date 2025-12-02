import pytest
from django.contrib.auth import authenticate

from apps.account.forms import RegisterForm
from apps.account.models import User


@pytest.mark.django_db
class TestRegisterForm:
    form_class = RegisterForm

    def test_register_new_user(self, form_request):
        new_data = {"name": "new_name", "email": "new_user_email@local.local", "password": "my_password"}

        form = self.form_class(data=new_data)
        assert form.is_valid()

        new_user = form.save()
        assert new_user.name == new_data["name"]
        assert new_user.email == new_data["email"]

        assert not new_user.is_guest
        assert new_user.is_active

        assert not new_user.is_superuser
        assert not new_user.is_staff

        authenticated_user = authenticate(request=form_request, email=new_data["email"], password=new_data["password"])
        assert authenticated_user == new_user

    def test_guest_registering_turns_into_non_guest_user(self, guest_user, form_request):
        assert guest_user.is_guest, "This test does not make sense if guest_user is no guest"

        new_data = {
            "id": guest_user.id,
            "is_guest": False,
            "name": "new_name",
            "email": "new_user_email@local.local",
            "password": "my_password",
        }

        form = self.form_class(instance=guest_user, data=new_data)
        assert form.is_valid()

        form.save()

        guest_user.refresh_from_db()

        assert guest_user.name == new_data["name"]
        assert guest_user.email == new_data["email"]

        assert not guest_user.is_guest
        assert guest_user.is_active

        assert not guest_user.is_superuser
        assert not guest_user.is_staff

        authenticated_user = authenticate(request=form_request, email=new_data["email"], password=new_data["password"])
        assert authenticated_user == guest_user

    def test_duplicate_email_raises_error(self, user):
        form = self.form_class(data={"email": user.email})
        assert not form.is_valid()

        assert form.errors["email"][0] == form.ExceptionMessage.EMAIL_ADDRESS_ALREADY_IN_USE.format(email=user.email)

    def test_duplicate_email_case_insensitive(self, user):
        uppercased = user.email.upper()
        form = self.form_class(
            data={"email": uppercased, "name": "name", "password": "password"},
        )
        assert not form.is_valid()

        expected_email = User.objects.normalize_email(uppercased)
        assert form.errors["email"][0] == form.ExceptionMessage.EMAIL_ADDRESS_ALREADY_IN_USE.format(
            email=expected_email
        )
