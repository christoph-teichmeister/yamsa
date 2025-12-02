import factory
from faker import Faker

from apps.account.tests.factories import UserFactory
from apps.webpush.models import WebpushInformation

fake = Faker()


class WebpushInformationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WebpushInformation

    user = factory.SubFactory(UserFactory)
    browser = factory.LazyFunction(lambda: fake.user_agent()[:100])
    user_agent = factory.Faker("user_agent")
    endpoint = factory.Faker("url")
    auth = factory.Faker("uuid4")
    p256dh = factory.Faker("uuid4")
