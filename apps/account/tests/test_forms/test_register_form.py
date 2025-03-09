from django.contrib.auth import authenticate
from django.test import RequestFactory

from apps.account.forms import RegisterForm
from apps.core.tests.setup import BaseTestSetUp


class RegisterFormTestCase(BaseTestSetUp):
    form = RegisterForm

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.request = RequestFactory().get("/")

    def test_register_new_user(self):
        new_data = {"name": "new_name", "email": "new_user_email@local.local", "password": "my_password"}

        form = self.form(data=new_data)
        self.assertTrue(form.is_valid())

        new_user = form.save()
        self.assertEqual(new_user.name, new_data["name"])
        self.assertEqual(new_user.email, new_data["email"])

        self.assertFalse(new_user.is_guest)
        self.assertTrue(new_user.is_active)

        self.assertFalse(new_user.is_superuser)
        self.assertFalse(new_user.is_staff)

        user = authenticate(request=self.request, email=new_data["email"], password=new_data["password"])
        self.assertEqual(new_user, user)

    def test_guest_registering_turns_into_non_guest_user(self):
        self.assertTrue(self.guest_user.is_guest, "This test does not make sense if guest_user is no guest")

        new_data = {
            "id": self.guest_user.id,
            "is_guest": False,
            "name": "new_name",
            "email": "new_user_email@local.local",
            "password": "my_password",
        }

        form = self.form(instance=self.guest_user, data=new_data)
        self.assertTrue(form.is_valid())

        form.save()

        self.guest_user.refresh_from_db()

        self.assertEqual(self.guest_user.name, new_data["name"])
        self.assertEqual(self.guest_user.email, new_data["email"])

        self.assertFalse(self.guest_user.is_guest)
        self.assertTrue(self.guest_user.is_active)

        self.assertFalse(self.guest_user.is_superuser)
        self.assertFalse(self.guest_user.is_staff)

        user = authenticate(request=self.request, email=new_data["email"], password=new_data["password"])
        self.assertEqual(self.guest_user, user)

    def test_duplicate_email_raises_error(self):
        form = self.form(data={"email": self.user.email})
        self.assertFalse(form.is_valid())

        self.assertEqual(
            form.errors["email"][0], form.ExceptionMessage.EMAIL_ADDRESS_ALREADY_IN_USE.format(email=self.user.email)
        )
