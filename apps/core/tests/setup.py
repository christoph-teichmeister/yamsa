from django.test import Client, TestCase, override_settings
from model_bakery import baker

from apps.account.models import User


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
        cls.client.force_login(user)
        return cls.client
