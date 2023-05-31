from django.test import Client, TestCase, override_settings
from model_bakery import baker

from apps.account.tests.baker_recipes import default_password


@override_settings(
    STATICFILES_STORAGE="django.contrib.staticfiles.storage.StaticFilesStorage"
)
class BaseTestSetUp(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.superuser = baker.make_recipe("apps.account.tests.superuser")
        cls.reauthenticate_user(cls.superuser)

    @classmethod
    def reauthenticate_user(cls, user):
        cls.client = Client()
        login = cls.client.login(username=user.username, password=default_password)
        cls.assertTrue(cls(), login)
