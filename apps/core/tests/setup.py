from django.test import Client, RequestFactory, TestCase, override_settings
from model_bakery import baker

from apps.account.models import User
from apps.account.tests.baker_recipes import default_password


@override_settings(STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage")
class BaseTestSetUp(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = baker.make_recipe("apps.account.tests.user")
        cls.guest_user = baker.make_recipe("apps.account.tests.guest_user")

        cls.room = baker.make_recipe("apps.room.tests.room")
        cls.room.users.add(cls.user, cls.guest_user)

        cls.superuser = baker.make_recipe("apps.account.tests.superuser")

        cls.client = cls.reauthenticate_user(cls.user)

    @classmethod
    def reauthenticate_user(cls, user: User) -> Client:
        cls.client = Client()
        cls.client.defaults["HTTP_HX_REQUEST"] = "true"
        # Create a request object for django-axes
        request = RequestFactory().get("/")

        login = cls.client.login(request=request, email=user.email, password=default_password)
        cls.assertTrue(cls(), login, f"{login=}")

        return cls.client
