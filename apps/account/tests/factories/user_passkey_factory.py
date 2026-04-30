import factory
from factory import Sequence
from passkeys.models import UserPasskey

from apps.account.tests.factories.user_factory import UserFactory


class UserPasskeyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserPasskey

    user = factory.SubFactory(UserFactory)
    name = Sequence(lambda n: f"Test Key {n}")
    enabled = True
    platform = "Key"
    credential_id = Sequence(lambda n: f"credential-id-{n}")
    token = "dGVzdA"
