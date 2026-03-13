import factory
from factory import Faker, Sequence

from apps.transaction.models import Category


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    slug = Sequence(lambda sequence: f"category-{sequence}")
    name = Faker("word")
    emoji = "💰"
    color = "#E0E0E0"
    is_default = False
